#!/usr/bin/env python3
"""
Evaluation Runner

Measures retrieval and generation quality against
data/test-queries/evaluation_dataset.csv.

For each query with ground-truth `relevant_documents`, computes Recall@5,
Recall@10 and MRR separately for keyword-only, semantic-only, and hybrid
retrieval (the comparison called for in docs/IMPLEMENTATION_PLAN.md Phase
4.5/8.2). For every query, also runs the full generation pipeline (same
steps as app/api/chat.py) and scores the answer for groundedness using GPT-4o-mini as the judge model - a different checkpoint
than the GPT-4o answer-generator, though not a fully independent vendor
(Anthropic/Gemini keys were not reliably usable in this environment at
the time this was written; swap in a genuinely separate provider if one
becomes available, to reduce self-grading bias). Also scores citation
validity and response latency.

This is an automated proxy for the "Answer Correctness (human eval)"
target in the plan, not a replacement for it - a sample of responses
should still be spot-checked by a human before quoting these numbers in
the thesis.

Usage:
    python scripts/evaluate.py [--limit N] [--skip-generation] [--output path.json]
"""
import argparse
import asyncio
import csv
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models import Document
from app.core.config import settings
from app.services.roman_urdu import LanguageDetector, RomanUrduNormalizer
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.rag.prompt import create_rag_prompt
from app.services.rag.llm_provider import get_llm_provider
from app.services.analytics.topic_classifier import classify as classify_topic

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'test-queries', 'evaluation_dataset.csv'
)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'test-queries', 'eval_results.json'
)

NO_ANSWER_MARKERS = [
    "i don't have enough information",
    "i couldn't find relevant information",
]

JUDGE_SYSTEM = """You are evaluating a RAG chatbot's answer for factual groundedness.
Given the SOURCE CONTEXT the chatbot was given, and its RESPONSE, rate whether every
factual claim in the response is actually supported by the source context.

Respond with ONLY a JSON object, no other text:
{"verdict": "grounded" | "partially_grounded" | "not_grounded", "reason": "<one sentence>"}

- "grounded": every factual claim is directly supported by the context, no invented facts
- "partially_grounded": most claims supported, but some detail is unsupported or invented
- "not_grounded": response makes claims not supported by the context, or contradicts it
"""

language_detector = LanguageDetector()
normalizer = RomanUrduNormalizer(use_translation=False)


def load_dataset(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('query') is None:
                continue
            rows.append({
                'query': row.get('query', ''),
                'expected_language': (row.get('expected_language') or '').strip(),
                'expected_topic': (row.get('expected_topic') or '').strip(),
                'relevant_documents': [
                    d.strip() for d in (row.get('relevant_documents') or '').split(';') if d.strip()
                ],
                'notes': row.get('notes', ''),
            })
    return rows


def is_no_answer(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in NO_ANSWER_MARKERS)


def chunk_titles(results, db):
    titles = []
    for item in results:
        chunk = item[0]
        doc = db.query(Document).filter_by(id=chunk.doc_id).first()
        titles.append(doc.title if doc else None)
    return titles


def compute_recall_mrr(retrieved_titles, relevant_docs):
    if not relevant_docs:
        return None
    relevant_set = set(relevant_docs)
    top5 = retrieved_titles[:5]
    top10 = retrieved_titles[:10]
    mrr = 0.0
    for i, t in enumerate(retrieved_titles):
        if t in relevant_set:
            mrr = 1.0 / (i + 1)
            break
    return {
        'recall@5': 1.0 if any(t in relevant_set for t in top5) else 0.0,
        'recall@10': 1.0 if any(t in relevant_set for t in top10) else 0.0,
        'mrr': mrr,
    }


def evaluate_retrieval(retriever, query, db, relevant_docs, top_k=25):
    kw = retriever._keyword_search(query, db, top_k=top_k)
    sem = retriever._semantic_search(query, db, top_k=top_k)
    hybrid = retriever.retrieve(query=query, db=db, top_k=top_k, use_hybrid=True)

    return {
        'keyword': compute_recall_mrr(chunk_titles(kw, db), relevant_docs),
        'semantic': compute_recall_mrr(chunk_titles(sem, db), relevant_docs),
        'hybrid': compute_recall_mrr(chunk_titles(hybrid, db), relevant_docs),
    }


async def run_generation(query, db, retriever, llm_provider):
    start = time.time()
    lang, _ = language_detector.detect(query)
    normalized = normalizer.normalize(query) if lang in ('ur', 'mixed') else query

    results = retriever.retrieve(query=normalized, db=db, top_k=25, use_hybrid=True)
    if not results:
        return {
            'response': "I couldn't find relevant information about this in the admission documents.",
            'citations': [],
            'cited_documents': [],
            'has_citation_markers': False,
            'citation_markers_valid': None,
            'latency_ms': int((time.time() - start) * 1000),
            'language': lang,
            'provider': 'none',
            'topic_predicted': classify_topic(normalized),
            'context_for_judge': '',
        }

    chunks = [c for c, s, m in results]
    documents = {}
    for c, s, m in results:
        doc = db.query(Document).filter_by(id=c.doc_id).first()
        if doc:
            documents[str(c.doc_id)] = doc.title

    system_prompt, user_prompt, citations = create_rag_prompt(
        query=query, chunks=chunks, documents=documents, max_chunks=10
    )

    try:
        response_text = await llm_provider.generate(
            prompt=user_prompt, system_prompt=system_prompt, temperature=0.3, max_tokens=1024
        )
        provider_name = llm_provider.get_current_provider()
    except Exception as e:
        response_text = f"[ERROR: {e}]"
        provider_name = 'error'

    latency_ms = int((time.time() - start) * 1000)

    marker_indices = re.findall(r'\[(\d+)\]', response_text)
    citation_markers_valid = (
        all(1 <= int(m) <= len(citations) for m in marker_indices) if marker_indices else None
    )
    cited_documents = set()
    for m in marker_indices:
        idx = int(m) - 1
        if 0 <= idx < len(citations):
            cited_documents.add(citations[idx].document_title)

    return {
        'response': response_text,
        'citations': [c.format() for c in citations],
        'cited_documents': sorted(cited_documents),
        'has_citation_markers': len(marker_indices) > 0,
        'citation_markers_valid': citation_markers_valid,
        'latency_ms': latency_ms,
        'language': lang,
        'provider': provider_name,
        'topic_predicted': classify_topic(normalized),
        'context_for_judge': "\n\n".join(f"[{i + 1}] {c.content}" for i, c in enumerate(chunks[:10])),
    }


def make_judge_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)


async def judge_response(judge_client, query, response_text, context):
    if is_no_answer(response_text) or not context.strip():
        return {'verdict': 'no_answer_given', 'reason': 'declined to answer or no context'}
    if response_text.startswith('[ERROR:'):
        return {'verdict': 'error', 'reason': response_text}

    user_prompt = f"SOURCE CONTEXT:\n{context}\n\nQUERY: {query}\n\nRESPONSE: {response_text}"
    try:
        completion = await judge_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        raw = completion.choices[0].message.content or ""
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {'verdict': 'unparseable', 'reason': raw[:200]}
    except Exception as e:
        return {'verdict': 'error', 'reason': str(e)}


def percentile(values, pct):
    if not values:
        return None
    s = sorted(values)
    idx = min(len(s) - 1, int(len(s) * pct))
    return s[idx]


def summarize(per_query):
    retrieval_rows = [r for r in per_query if r.get('retrieval')]
    summary = {'retrieval': {}, 'generation': {}, 'by_language': {}}

    for mode in ('keyword', 'semantic', 'hybrid'):
        vals = [r['retrieval'][mode] for r in retrieval_rows if r['retrieval'].get(mode)]
        if vals:
            summary['retrieval'][mode] = {
                'recall@5': statistics.mean(v['recall@5'] for v in vals),
                'recall@10': statistics.mean(v['recall@10'] for v in vals),
                'mrr': statistics.mean(v['mrr'] for v in vals),
                'n': len(vals),
            }

    gen_rows = [r for r in per_query if r.get('generation')]
    if gen_rows:
        no_answer_rate = statistics.mean(
            1.0 if is_no_answer(r['generation']['response']) else 0.0 for r in gen_rows
        )
        valid_flags = [
            r['generation']['citation_markers_valid'] for r in gen_rows
            if r['generation']['citation_markers_valid'] is not None
        ]
        citation_valid_rate = statistics.mean(1.0 if v else 0.0 for v in valid_flags) if valid_flags else None
        latencies = [r['generation']['latency_ms'] for r in gen_rows]
        verdicts = [r.get('judge', {}).get('verdict') for r in gen_rows]
        grounded_rate = statistics.mean(
            1.0 if v in ('grounded', 'partially_grounded') else 0.0 for v in verdicts if v
        ) if verdicts else None
        topic_matches = [
            1.0 if r['expected_topic'] and r['generation']['topic_predicted'] == r['expected_topic'] else 0.0
            for r in gen_rows if r['expected_topic']
        ]

        summary['generation'] = {
            'n': len(gen_rows),
            'no_answer_rate': no_answer_rate,
            'citation_valid_rate': citation_valid_rate,
            'grounded_or_partial_rate': grounded_rate,
            'avg_latency_ms': statistics.mean(latencies),
            'p95_latency_ms': percentile(latencies, 0.95),
            'topic_classification_accuracy': statistics.mean(topic_matches) if topic_matches else None,
        }

        for lang in ('en', 'ur', 'mixed'):
            lang_rows = [r for r in gen_rows if r['expected_language'] == lang]
            if not lang_rows:
                continue
            lang_verdicts = [r.get('judge', {}).get('verdict') for r in lang_rows]
            success_rate = statistics.mean(
                1.0 if v in ('grounded', 'partially_grounded') else 0.0 for v in lang_verdicts if v
            ) if lang_verdicts else None
            summary['by_language'][lang] = {
                'n': len(lang_rows),
                'success_rate': success_rate,
                'avg_latency_ms': statistics.mean(r['generation']['latency_ms'] for r in lang_rows),
            }

    return summary


def print_summary(summary):
    print("\n" + "=" * 60)
    print("RETRIEVAL METRICS (averaged over queries with ground truth)")
    print("=" * 60)
    for mode, m in summary['retrieval'].items():
        print(f"  {mode:10s}  Recall@5={m['recall@5']:.1%}  Recall@10={m['recall@10']:.1%}  "
              f"MRR={m['mrr']:.3f}  (n={m['n']})")

    g = summary.get('generation') or {}
    if g:
        print("\n" + "=" * 60)
        print("GENERATION METRICS")
        print("=" * 60)
        print(f"  No-answer rate:              {g['no_answer_rate']:.1%}")
        if g['citation_valid_rate'] is not None:
            print(f"  Citation marker validity:     {g['citation_valid_rate']:.1%}")
        if g['grounded_or_partial_rate'] is not None:
            print(f"  Grounded/partial (LLM judge): {g['grounded_or_partial_rate']:.1%}  "
                  f"<- proxy for Answer Correctness, verify with human sample")
        print(f"  Avg latency:                  {g['avg_latency_ms'] / 1000:.2f}s")
        print(f"  P95 latency:                  {g['p95_latency_ms'] / 1000:.2f}s")
        if g['topic_classification_accuracy'] is not None:
            print(f"  Topic classification accuracy:{g['topic_classification_accuracy']:.1%}")

        print("\n" + "=" * 60)
        print("BY LANGUAGE")
        print("=" * 60)
        for lang, stats in summary['by_language'].items():
            sr = f"{stats['success_rate']:.1%}" if stats['success_rate'] is not None else "n/a"
            print(f"  {lang:6s}  success_rate={sr}  avg_latency={stats['avg_latency_ms'] / 1000:.2f}s  (n={stats['n']})")

    print("\n" + "=" * 60)
    print("VS. THESIS SUCCESS CRITERIA (docs/IMPLEMENTATION_PLAN.md)")
    print("=" * 60)
    hybrid = summary['retrieval'].get('hybrid', {})
    if hybrid:
        r5 = hybrid['recall@5']
        print(f"  Retrieval Recall@5 > 80%:     {r5:.1%}  {'PASS' if r5 > 0.8 else 'FAIL'}")
    if g.get('citation_valid_rate') is not None:
        cv = g['citation_valid_rate']
        print(f"  Citation Accuracy > 90%:      {cv:.1%}  {'PASS' if cv > 0.9 else 'FAIL'}")
    if g:
        avg_s = g['avg_latency_ms'] / 1000
        print(f"  Avg Response Time < 3s:       {avg_s:.2f}s  {'PASS' if avg_s < 3 else 'FAIL'}")
    ur = summary['by_language'].get('ur')
    mixed = summary['by_language'].get('mixed')
    ur_rows = [x for x in (ur, mixed) if x and x['success_rate'] is not None]
    if ur_rows:
        ur_success = statistics.mean(x['success_rate'] for x in ur_rows)
        print(f"  Roman Urdu Success > 70%:     {ur_success:.1%}  {'PASS' if ur_success > 0.7 else 'FAIL'}")


async def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval + generation quality")
    parser.add_argument('--limit', type=int, default=None, help="Only run the first N queries")
    parser.add_argument('--skip-generation', action='store_true', help="Retrieval metrics only (fast, no LLM calls)")
    parser.add_argument('--output', default=DEFAULT_OUTPUT, help="Path to write detailed JSON results")
    args = parser.parse_args()

    dataset = load_dataset(DATASET_PATH)
    if args.limit:
        dataset = dataset[:args.limit]

    db = SessionLocal()
    retriever = HybridRetriever()
    llm_provider = get_llm_provider() if not args.skip_generation else None
    judge = make_judge_client() if not args.skip_generation else None

    per_query = []
    for i, row in enumerate(dataset):
        query = row['query'].strip()
        print(f"[{i + 1}/{len(dataset)}] {query!r}")

        result = {
            'query': query,
            'expected_language': row['expected_language'],
            'expected_topic': row['expected_topic'],
            'relevant_documents': row['relevant_documents'],
            'notes': row['notes'],
        }

        if not query:
            # Empty-query edge case: exercise the pipeline's guard behavior only.
            result['generation'] = {'response': '[skipped: empty query]', 'latency_ms': 0}
            per_query.append(result)
            continue

        if row['relevant_documents']:
            result['retrieval'] = evaluate_retrieval(retriever, query, db, row['relevant_documents'])

        if not args.skip_generation:
            gen = await run_generation(query, db, retriever, llm_provider)
            result['generation'] = gen
            result['judge'] = await judge_response(judge, query, gen['response'], gen['context_for_judge'])

        per_query.append(result)

    db.close()

    summary = summarize(per_query)
    print_summary(summary)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'per_query': per_query}, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results written to {args.output}")


if __name__ == '__main__':
    asyncio.run(main())
