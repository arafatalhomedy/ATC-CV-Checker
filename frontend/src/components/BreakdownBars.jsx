const LABELS = {
  keyword_coverage: 'Keyword coverage',
  cosine_similarity: 'Vocabulary overlap',
  section_completeness: 'Section structure',
  contact_info: 'Contact info',
  format_risk: 'Format safety',
}

const WEIGHTS = {
  keyword_coverage: 0.45,
  cosine_similarity: 0.15,
  section_completeness: 0.20,
  contact_info: 0.10,
  format_risk: 0.10,
}

export default function BreakdownBars({ scores }) {
  return (
    <div className="breakdown">
      <div className="panel-label">Score breakdown</div>
      {Object.entries(scores).map(([key, value]) => (
        <div className="breakdown-row" key={key}>
          <div className="breakdown-row-top">
            <span className="breakdown-name">{LABELS[key] || key}</span>
            <span className="breakdown-weight">weight {Math.round(WEIGHTS[key] * 100)}%</span>
            <span className="breakdown-value">{Math.round(value * 100)}%</span>
          </div>
          <div className="breakdown-track">
            <div
              className="breakdown-fill"
              style={{ width: `${Math.round(value * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
