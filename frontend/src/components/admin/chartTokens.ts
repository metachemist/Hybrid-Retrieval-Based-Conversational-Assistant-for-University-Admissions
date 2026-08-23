/**
 * Shared chart tokens.
 *
 * Every chart on this dashboard plots a SINGLE measure (a count), so there is
 * one series colour rather than a categorical palette — giving each bar its own
 * hue would double-encode bar length as colour and burn the only free channel
 * on information the chart already shows.
 *
 * SERIES_1 is primary-700. Checked with the data-viz palette validator against a
 * light surface: inside the L 0.43–0.77 band, over the 0.1 chroma floor, and
 * >= 3:1 contrast against the surface (primary-600 measured 2.86:1 and would
 * have needed a relief treatment).
 */
export const SERIES_1 = '#537d17'

/** One step off the surface — hairline, solid, recessive. Never dashed. */
export const GRID = '#e7e7e4'

/** Axis + tick text uses a text token, never the data colour. */
export const AXIS_TEXT = '#737776'

/** Surface colour, used for the 2px ring on markers that overlap the line. */
export const SURFACE = '#ffffff'

export const AXIS_TICK = { fontSize: 11, fill: AXIS_TEXT, fontFamily: 'var(--font-mono)' }
