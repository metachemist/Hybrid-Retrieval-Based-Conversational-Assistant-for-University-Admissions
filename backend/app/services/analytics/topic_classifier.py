"""
Keyword-based topic classifier for admission queries.

Classifies against the normalized query so Roman Urdu terms already
translated by the normalizer still match English keywords.
"""
import re

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "eligibility": [
        "eligible", "eligibility", "qualify", "qualification", "criteria",
        "marks", "percentage", "inter", "intermediate", "matric", "matriculation",
        "minimum", "required marks", "aggregate", "hssc", "ssc",
    ],
    "fees": [
        "fee", "fees", "payment", "cost", "amount", "charges", "voucher",
        "tuition", "prospectus fee", "kitna", "paisa", "rupee", "rs",
    ],
    "documents": [
        "document", "documents", "certificate", "transcript", "photo",
        "photograph", "attested", "original", "copy", "copies", "dmcs",
        "domicile", "cnic", "docs", "kagaz", "papers",
    ],
    "deadlines": [
        "deadline", "last date", "last day", "closing date", "schedule",
        "closing", "when", "date", "kab", "expire", "submission date",
    ],
    "merit": [
        "merit", "merit list", "result", "selected", "selection", "rank",
        "position", "waiting list", "marit", "cut off",
    ],
    "programs": [
        "program", "programme", "course", "department", "faculty", "bs",
        "ms", "mba", "bba", "bsc", "msc", "degree", "digree", "field",
        "subject", "discipline", "morning", "evening",
    ],
    "application": [
        "apply", "application", "how to apply", "submit", "submission",
        "form", "online", "process", "procedure", "registration",
        "enroll", "enrollment", "chahiye", "kaise",
    ],
}


# Whole-word / whole-phrase match, compiled once per keyword. Substring
# matching mislabelled queries: "date" fired on "candi**date**", "rs" on
# "cou**rs**es", "inter" on "**inter**net".
_KEYWORD_PATTERNS: dict[str, list[re.Pattern]] = {
    topic: [re.compile(r"\b" + re.escape(kw) + r"\b") for kw in keywords]
    for topic, keywords in TOPIC_KEYWORDS.items()
}


def classify(query: str) -> str:
    """
    Classify a query into one of the topic categories.

    Args:
        query: Normalized query text (lowercase preferred)

    Returns:
        Topic name or "general" if no match found
    """
    query_lower = query.lower()

    best_topic = "general"
    best_score = 0

    for topic, patterns in _KEYWORD_PATTERNS.items():
        score = sum(1 for pat in patterns if pat.search(query_lower))
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic
