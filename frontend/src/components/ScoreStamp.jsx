function scoreTier(score) {
  if (score >= 0.75) return { label: 'STRONG MATCH', tone: 'stamp--green' }
  if (score >= 0.5) return { label: 'NEEDS WORK', tone: 'stamp--amber' }
  return { label: 'WEAK MATCH', tone: 'stamp--red' }
}

export default function ScoreStamp({ score }) {
  const pct = Math.round(score * 100)
  const tier = scoreTier(score)

  return (
    <div className={`stamp ${tier.tone}`}>
      <div className="stamp-ring">
        <div className="stamp-pct">{pct}<span className="stamp-pct-sign">%</span></div>
        <div className="stamp-label">{tier.label}</div>
      </div>
    </div>
  )
}
