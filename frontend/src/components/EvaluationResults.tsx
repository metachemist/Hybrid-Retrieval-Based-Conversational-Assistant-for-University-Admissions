/**
 * Chapter 6 of the thesis, rendered for the landing page: the retrieval
 * comparison table, the headline generation figures, and the one result that
 * went against the hypothesis.
 *
 * Every number here is copied from THESIS_REPORT.md Sections 6.2 and 6.3. If
 * the evaluation is re-run, these must be updated together with the report --
 * they are the same claim made in two places.
 */

type Row = {
  method: string
  recall5: string
  recall10: string
  mrr: string
  /** The fused configuration the project actually ships. */
  primary?: boolean
}

const RETRIEVAL: Row[] = [
  { method: 'Keyword only', recall5: '76.3%', recall10: '84.2%', mrr: '0.701' },
  { method: 'Semantic only', recall5: '71.1%', recall10: '76.3%', mrr: '0.550' },
  { method: 'Hybrid (RRF)', recall5: '76.3%', recall10: '84.2%', mrr: '0.667', primary: true },
]

const GENERATION = [
  { value: '100%', label: 'Citation markers valid' },
  { value: '68.3%', label: 'Judged grounded or partial' },
  { value: '3.82s', label: 'Average latency' },
  { value: '5.80s', label: 'P95 latency' },
]

export default function EvaluationResults() {
  return (
    <div>
      {/* Retrieval comparison. Scrolls inside its own container on narrow
          viewports rather than forcing the page to scroll sideways. */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[34rem] border-collapse text-left">
          <caption className="sr-only">
            Retrieval accuracy by method, measured over 38 ground-truth-labelled queries
          </caption>
          <thead>
            <tr className="border-b border-white/20">
              {['Method', 'Recall@5', 'Recall@10', 'MRR'].map((h, i) => (
                <th
                  key={h}
                  scope="col"
                  className={`pb-3 font-mono text-[12px] font-normal uppercase tracking-tighter2 text-muted ${
                    i === 0 ? '' : 'text-right'
                  }`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {RETRIEVAL.map(({ method, recall5, recall10, mrr, primary }) => (
              <tr
                key={method}
                className={`border-b border-white/10 ${primary ? 'text-white' : 'text-neutral-400'}`}
              >
                <th
                  scope="row"
                  className={`py-4 pr-4 text-[15px] font-normal ${primary ? 'font-medium text-white' : ''}`}
                >
                  {primary && (
                    <span
                      className="mr-2.5 inline-block h-2 w-2 translate-y-[-1px] bg-primary-300"
                      aria-hidden="true"
                    />
                  )}
                  {method}
                </th>
                {[recall5, recall10, mrr].map((v, i) => (
                  <td
                    key={i}
                    className={`py-4 text-right font-mono text-[15px] tracking-tighter2 ${
                      primary ? 'text-primary-300' : ''
                    }`}
                  >
                    {v}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-5 font-mono text-[12px] tracking-tighter2 text-muted">
        n = 38 ground-truth-labelled queries, from a 41-query benchmark
      </p>

      {/* Generation-side headline figures */}
      <div className="mt-16 grid grid-cols-2 gap-x-8 gap-y-10 border-t border-white/20 pt-12 lg:grid-cols-4">
        {GENERATION.map(({ value, label }) => (
          <div key={label}>
            <p className="display-lg text-[clamp(2rem,4.4vw,3.2rem)] text-white">{value}</p>
            <p className="label-mono mt-3">{label}</p>
          </div>
        ))}
      </div>

      {/* The result that contradicted the hypothesis. Kept prominent on
          purpose: the honesty is the point of publishing the numbers at all. */}
      <div className="mt-16 border-l-2 border-primary-300 bg-white/[0.03] py-6 pl-6 pr-6 sm:pl-8">
        <p className="label-mono">Reported as measured</p>
        <p className="mt-4 max-w-[46rem] text-[15px] leading-[1.75] text-neutral-400">
          Hybrid retrieval matched keyword-only search on recall, and clearly beat semantic-only
          search on every metric, but it did <span className="text-white">not</span> beat
          keyword-only search on MRR (0.667 against 0.701). The literature predicts otherwise. The
          result is published as it came out, along with the likely cause: an OR-based keyword query
          that already recalls unusually well, leaving fusion little headroom to add.
        </p>
      </div>
    </div>
  )
}
