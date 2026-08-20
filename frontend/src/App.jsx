import { useState, useRef } from 'react'
import UploadPanel from './components/UploadPanel.jsx'
import ScoreStamp from './components/ScoreStamp.jsx'
import BreakdownBars from './components/BreakdownBars.jsx'
import KeywordMargin from './components/KeywordMargin.jsx'
import SuggestionsPanel from './components/SuggestionsPanel.jsx'
import { analyzeCV, optimizeCV } from './api.js'

export default function App() {
  const [report, setReport] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // Keep file + JD so we can re-send them to /api/optimize
  const lastFileRef = useRef(null)
  const lastJDRef = useRef('')

  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizedText, setOptimizedText] = useState('')
  const [optimizeError, setOptimizeError] = useState('')

  async function handleAnalyze(file, jobDescription) {
    setIsLoading(true)
    setError('')
    setReport(null)
    setOptimizedText('')
    setOptimizeError('')

    lastFileRef.current = file
    lastJDRef.current = jobDescription

    try {
      const data = await analyzeCV(file, jobDescription)
      setReport(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleOptimize() {
    if (!lastFileRef.current || !lastJDRef.current) return
    setIsOptimizing(true)
    setOptimizeError('')
    try {
      const text = await optimizeCV(lastFileRef.current, lastJDRef.current)
      setOptimizedText(text)
    } catch (err) {
      setOptimizeError(err.message)
    } finally {
      setIsOptimizing(false)
    }
  }

  return (
    <div className="page">
      <header className="masthead">
        <div className="masthead-title">CV Desk</div>
        <div className="masthead-subtitle">An ATS readability check — where your resume gets marked up before a recruiter ever sees it.</div>
      </header>

      <main className="layout">
        <UploadPanel onAnalyze={handleAnalyze} isLoading={isLoading} />

        <section className="results">
          {!report && !error && !isLoading && (
            <div className="results-placeholder">
              <div className="results-placeholder-mark">—</div>
              <p>Attach a resume and a job description to see how it reads to an ATS.</p>
            </div>
          )}

          {isLoading && (
            <div className="results-placeholder">
              <div className="results-placeholder-mark results-placeholder-mark--pulse">…</div>
              <p>Scanning your resume against the job description.</p>
            </div>
          )}

          {error && (
            <div className="error-box">
              <div className="error-box-title">Couldn&rsquo;t complete the check</div>
              <p>{error}</p>
            </div>
          )}

          {report && !isLoading && (
            <>
              <ScoreStamp score={report.final_score} />
              <BreakdownBars scores={report.component_scores} />
              <KeywordMargin
                keywords={report.keyword_table}
                missingSections={report.missing_sections}
                formatWarnings={report.format_warnings}
              />
              <SuggestionsPanel
                suggestions={report.suggestions || []}
                onOptimize={handleOptimize}
                isOptimizing={isOptimizing}
                optimizedText={optimizedText}
              />
              {optimizeError && (
                <div className="error-box">
                  <div className="error-box-title">Couldn&rsquo;t optimize</div>
                  <p>{optimizeError}</p>
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}
