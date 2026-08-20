const API_BASE = 'http://localhost:5000'

/**
 * Sends the CV file + job description to the backend and returns the
 * parsed ATS report. Throws an Error with a user-facing message on failure.
 */
export async function analyzeCV(file, jobDescription) {
  const formData = new FormData()
  formData.append('cv', file)
  formData.append('job_description', jobDescription)

  let response
  try {
    response = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error(
      "Can't reach the backend. Make sure the Flask server is running on port 5000."
    )
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(data?.error || 'Something went wrong analyzing the CV.')
  }

  return data
}

/**
 * Sends the CV file + job description to the optimise endpoint and
 * returns the optimised resume as plain text.
 */
export async function optimizeCV(file, jobDescription) {
  const formData = new FormData()
  formData.append('cv', file)
  formData.append('job_description', jobDescription)

  let response
  try {
    response = await fetch(`${API_BASE}/api/optimize`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error(
      "Can't reach the backend. Make sure the Flask server is running on port 5000."
    )
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.error || 'Something went wrong optimizing the CV.')
  }

  return await response.text()
}
