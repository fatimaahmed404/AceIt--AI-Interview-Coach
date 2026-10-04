import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getHistory, deleteSession } from "../api";
import { ScoreBar, scoreColor } from "../components/ui";

export default function History() {
  const [sessions, setSessions] = useState([]);
  const [filter, setFilter] = useState("overall_score");
  const [selected, setSelected] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getHistory().then(setSessions).catch(() => setSessions([]));
  }, []);

  const handleDelete = async (e, sessionId, index) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((_, i) => i !== index));
      if (selected === index) setSelected(null);
    } catch {
      alert("Could not delete. Make sure Flask is running.");
    }
  };

  const sorted = [...sessions].sort((a, b) => (b[filter] || 0) - (a[filter] || 0));

  const filters = [
    { key: "overall_score", label: "Overall" },
    { key: "confidence", label: "Confidence" },
    { key: "eye_contact_score", label: "Eye contact" },
    { key: "posture_score", label: "Posture" },
  ];

  return (
    <div style={{ maxWidth: 740, margin: "2rem auto", padding: "0 1rem" }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Past sessions</h2>
      <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 16 }}>
        Click a session to expand, or open the full scorecard.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        <span style={{ fontSize: 13, color: "var(--color-text-secondary)", alignSelf: "center" }}>Sort by:</span>
        {filters.map((f) => (
          <button key={f.key} onClick={() => setFilter(f.key)} style={{
            fontSize: 13, padding: "5px 14px", borderRadius: 8, cursor: "pointer", border: "0.5px solid",
            borderColor: filter === f.key ? "#534AB7" : "var(--color-border-tertiary)",
            background: filter === f.key ? "#EEEDFE" : "var(--color-background-primary)",
            color: filter === f.key ? "#3C3489" : "var(--color-text-primary)",
            fontWeight: filter === f.key ? 500 : 400,
          }}>{f.label}</button>
        ))}
      </div>

      {sessions.length === 0 && (
        <p style={{ color: "var(--color-text-secondary)" }}>No sessions yet. Record your first answer!</p>
      )}

      <div style={{ display: "grid", gap: 10 }}>
        {sorted.map((s, i) => (
          <div key={s._id || i} onClick={() => setSelected(selected === i ? null : i)} style={{
            background: "var(--color-background-secondary)", borderRadius: 12, border: "0.5px solid",
            borderColor: selected === i ? "#534AB7" : "var(--color-border-tertiary)",
            overflow: "hidden", cursor: "pointer",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px" }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8, display: "flex", alignItems: "center",
                justifyContent: "center", fontWeight: 600, fontSize: 15, flexShrink: 0,
                background: "var(--color-background-primary)", color: scoreColor(s.overall_score),
              }}>{s.overall_score ?? "–"}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {s.question}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: "var(--color-text-secondary)" }}>
                  {s.date ? new Date(s.date).toLocaleString() : ""}
                </p>
              </div>
              <button onClick={(e) => { e.stopPropagation(); navigate("/results", { state: s }); }} style={openBtn}>Open</button>
              <button onClick={(e) => handleDelete(e, s._id, i)} style={delBtn}>Delete</button>
            </div>

            {selected === i && (
              <div style={{ borderTop: "0.5px solid var(--color-border-tertiary)", padding: "16px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 12 }}>
                  <div>
                    <p style={sectionLabel}>Voice & text</p>
                    <ScoreBar label="Confidence" value={s.confidence} />
                    <ScoreBar label="Relevance" value={s.relevance} />
                    <ScoreBar label="Professionalism" value={s.professionalism} />
                    <ScoreBar label="Speaking" value={s.audio_score} />
                  </div>
                  <div>
                    <p style={sectionLabel}>Visual (Deep Learning)</p>
                    <ScoreBar label="Facial expression" value={s.expression_score} />
                    <ScoreBar label="Eye contact" value={s.eye_contact_score} />
                    <ScoreBar label="Posture" value={s.posture_score} />
                    <ScoreBar label="Head movement" value={s.head_movement_score} />
                  </div>
                </div>
                {s.transcript && (
                  <div style={{ background: "var(--color-background-primary)", borderRadius: 8, padding: "10px 12px" }}>
                    <p style={{ fontSize: 11, color: "var(--color-text-secondary)", margin: "0 0 6px" }}>Transcript</p>
                    <p style={{ fontSize: 13, lineHeight: 1.6, margin: 0 }}>{s.transcript}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const sectionLabel = { fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", margin: "0 0 8px" };
const openBtn = { background: "#EEEDFE", border: "0.5px solid #534AB7", borderRadius: 6, color: "#3C3489", fontSize: 12, padding: "4px 10px", cursor: "pointer", flexShrink: 0 };
const delBtn = { background: "#FCEBEB", border: "0.5px solid #F09595", borderRadius: 6, color: "#791F1F", fontSize: 12, padding: "4px 10px", cursor: "pointer", flexShrink: 0 };
