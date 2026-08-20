import { useState, useRef } from 'react'

const ACCEPTED_TYPES = ['.pdf', '.docx']

export default function UploadPanel({ onAnalyze, isLoading }) {
  const [file, setFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [validationError, setValidationError] = useState('')
  const fileInputRef = useRef(null)

  function validateAndSetFile(candidate) {
    if (!candidate) return
    const ext = candidate.name.slice(candidate.name.lastIndexOf('.')).toLowerCase()
    if (!ACCEPTED_TYPES.includes(ext)) {
      setValidationError('Only .pdf and .docx files are accepted.')
      return
    }
    setValidationError('')
    setFile(candidate)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    validateAndSetFile(e.dataTransfer.files[0])
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!file) {
      setValidationError('Attach a resume first.')
      return
    }
    if (!jobDescription.trim()) {
      setValidationError('Paste the job description you\u2019re applying to.')
      return
    }
    setValidationError('')
    onAnalyze(file, jobDescription)
  }

  return (
    <form className="upload-panel" onSubmit={handleSubmit}>
      <div className="panel-label">01 — Attach resume</div>

      <div
        className={`dropzone ${isDragging ? 'dropzone--active' : ''} ${file ? 'dropzone--filled' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click() }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          hidden
          onChange={(e) => validateAndSetFile(e.target.files[0])}
        />
        {file ? (
          <>
            <div className="dropzone-filename">{file.name}</div>
            <div className="dropzone-hint">Click to replace</div>
          </>
        ) : (
          <>
            <div className="dropzone-title">Drop your resume here</div>
            <div className="dropzone-hint">or click to browse — .pdf or .docx</div>
          </>
        )}
      </div>

      <div className="panel-label">02 — Paste the job description</div>
      <textarea
        className="jd-textarea"
        placeholder="Paste the full job posting here — requirements, responsibilities, all of it. More text means a more accurate keyword read."
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        rows={10}
      />

      {validationError && <div className="validation-error">{validationError}</div>}

      <button type="submit" className="analyze-button" disabled={isLoading}>
        {isLoading ? 'Reading your resume…' : 'Check my resume'}
      </button>
    </form>
  )
}
