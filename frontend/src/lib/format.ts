/**
 * Shared formatting helpers.
 */

/**
 * Render a millisecond duration for humans: sub-second stays in `ms`, anything
 * from a second up switches to one-decimal seconds. The unit travels with the
 * number so it is never ambiguous.
 */
export function formatLatency(ms: number): string {
  if (!Number.isFinite(ms)) return '--'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`
}
