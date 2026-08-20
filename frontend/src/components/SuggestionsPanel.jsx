import { useState } from 'react'

const CATEGORY_META = {
  keywords: { icon: '🔑', label: 'Keywords' },
  structure: { icon: '📄', label: 'Structure' },
  format: { icon: '⚠️', label: 'Format' },
  contact: { icon: '📬', label: 'Contact' },
}

const PRIORITY_CLASS = {
  high: 'suggestion-item--high',
  medium: 'suggestion-item--medium',
  low: 'suggestion-item--low',
}

export default function SuggestionsPanel({
  suggestions,
  onOptimize,
  isOptimizing,
  optimizedText,
}) {
  const [showPreview, setShowPreview] = useState(false)

  // Group by category
  const grouped = {}
  for (const s of suggestions) {
    if (!grouped[s.category]) grouped[s.category] = []
    grouped[s.category].push(s)
  }

  function handleDownload() {
    const blob = new Blob([optimizedText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'optimized_resume.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="suggestions-panel">
      <div className="panel-label">💡 Improvement suggestions</div>

      {suggestions.length === 0 ? (
        <p className="suggestions-empty">
          Your resume looks great — no major suggestions!
        </p>
      ) : (
        <div className="suggestions-list">
          {Object.entries(grouped).map(([category, items]) => {
            const meta = CATEGORY_META[category] || { icon: '💡', label: category }
            return (
              <div className="suggestions-category" key={category}>
                <div className="suggestions-category-title">
                  <span className="suggestions-category-icon">{meta.icon}</span>
                  {meta.label}
                </div>
                {items.map((item, i) => (
                  <div
                    className={`suggestion-item ${PRIORITY_CLASS[item.priority] || ''}`}
                    key={i}
                  >
                    <span className="suggestion-priority-badge">
                      {item.priority}
                    </span>
                    <span className="suggestion-text">{item.text}</span>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}

      {/* Optimize CTA */}
      <div className="optimize-cta">
        <div className="optimize-cta-divider" />
        <div className="optimize-cta-header">
          <div className="optimize-cta-title">✨ Auto-optimize your resume</div>
          <p className="optimize-cta-description">
            Restructure your resume for better ATS compatibility — using only the
            skills and experience you already have. Nothing fake is added.
          </p>
        </div>

        {!optimizedText ? (
          <button
            className="optimize-button"
            onClick={onOptimize}
            disabled={isOptimizing}
          >
            {isOptimizing ? 'Optimizing…' : 'Optimize my resume'}
          </button>
        ) : (
          <div className="optimize-result">
            <div className="optimize-result-actions">
              <button
                className="optimize-toggle-button"
                onClick={() => setShowPreview((p) => !p)}
              >
                {showPreview ? 'Hide preview' : 'Preview optimized resume'}
              </button>
              <button className="optimize-download-button" onClick={handleDownload}>
                ↓ Download .txt
              </button>
            </div>

            {showPreview && (
              <pre className="optimize-preview">{optimizedText}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
