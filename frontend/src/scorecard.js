/* Shared helper: convert the backend /analyze-full response into a flat
   session document used by History / Results / Progress. Kept in a plain .js
   module so it can be imported by multiple components without breaking
   React Fast Refresh. */
export function flattenScorecard(question, transcript, result) {
  const text = result?.text || {}
  const visual = result?.visual || {}
  const voice = result?.voice || {}
  const fe = visual.facial_expression || {}
  const ec = visual.eye_contact || {}
  const po = visual.posture || {}
  const hm = visual.head_movement || {}
  return {
    question,
    transcript: transcript || text.transcript || '',
    confidence: text.confidence ?? null,
    professionalism: text.professionalism ?? null,
    relevance: text.relevance ?? null,
    audio_score: voice.audio_score ?? null,
    eye_contact_percentage: ec.percentage ?? null,
    eye_contact_score: ec.score ?? null,
    posture_percentage: po.good_posture_percentage ?? null,
    posture_score: po.score ?? null,
    expression_dominant: fe.dominant ?? null,
    expression_score: fe.score ?? null,
    head_stability: hm.stability ?? null,
    head_movement_score: hm.score ?? null,
    overall_score: result?.overall?.score ?? null,
    visual_meta: visual.meta || null,
    visual_error: visual.error || null,
    timeline: result?.timeline || [],
    feedback: result?.feedback || [],
  }
}
