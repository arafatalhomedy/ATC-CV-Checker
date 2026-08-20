export default function KeywordMargin({ keywords, missingSections, formatWarnings }) {
  const found = keywords.filter((k) => k.found_in_cv)
  const missing = keywords.filter((k) => !k.found_in_cv)

  return (
    <div className="margin-notes">
      <div className="panel-label">Margin notes</div>

      <div className="notes-group">
        <div className="notes-group-title notes-group-title--found">
          Found in your resume ({found.length})
        </div>
        <div className="chip-row">
          {found.length === 0 && <span className="notes-empty">None of the top keywords matched.</span>}
          {found.map((k) => (
            <span className="chip chip--found" key={k.keyword}>{k.keyword}</span>
          ))}
        </div>
      </div>

      <div className="notes-group">
        <div className="notes-group-title notes-group-title--missing">
          Missing from your resume ({missing.length})
        </div>
        <div className="chip-row">
          {missing.length === 0 && <span className="notes-empty">Nothing missing — great coverage.</span>}
          {missing.map((k) => (
            <span className="chip chip--missing" key={k.keyword}>{k.keyword}</span>
          ))}
        </div>
      </div>

      {(missingSections.length > 0 || formatWarnings.length > 0) && (
        <div className="notes-group">
          <div className="notes-group-title notes-group-title--missing">Structure &amp; format</div>
          <ul className="notes-list">
            {missingSections.map((s) => (
              <li key={s}>Missing section: <strong>{s}</strong></li>
            ))}
            {formatWarnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
