import React from 'react'

function MetricsPage({ summary, riskData }) {
  const getRisksByFile = () => {
    const fileRisks = {}
    Object.entries(riskData.files).forEach(([filename, data]) => {
      fileRisks[filename] = {
        critical: data.risks.filter(r => r.severity === 'CRITICAL').length,
        high: data.risks.filter(r => r.severity === 'HIGH').length,
        medium: data.risks.filter(r => r.severity === 'MEDIUM').length,
        total: data.risks.length
      }
    })
    return fileRisks
  }

  const fileRisks = getRisksByFile()
  const totalIssues = summary.total
  const criticalPercent = Math.round((summary.critical / totalIssues) * 100)
  const highPercent = Math.round((summary.high / totalIssues) * 100)
  const mediumPercent = Math.round((summary.medium / totalIssues) * 100)

  const getRiskLevel = () => {
    if (summary.critical > 5) return { level: 'CRITICAL', color: '#ff4336', message: 'Immediate action required!' }
    if (summary.critical > 0) return { level: 'HIGH', color: '#ffa500', message: 'Fix before deployment' }
    if (summary.high > 5) return { level: 'MODERATE', color: '#ffc107', message: 'Should be addressed' }
    return { level: 'LOW', color: '#4caf50', message: 'Keep improving' }
  }

  const assessment = getRiskLevel()

  return (
    <div>
      <div style={{ marginBottom: '30px', textAlign: 'center' }}>
        <h2 style={{ color: assessment.color, marginBottom: '10px' }}>Overall Risk Assessment</h2>
        <div style={{ fontSize: '2.5em', fontWeight: 'bold', color: assessment.color, marginBottom: '10px' }}>
          {assessment.level}
        </div>
        <p style={{ color: '#a0a0a0', fontSize: '1.1em' }}>{assessment.message}</p>
      </div>

      <div className="metrics-grid">
        <div className="metric-card" style={{ borderLeft: '4px solid #ff4336' }}>
          <div className="metric-label">CRITICAL Issues</div>
          <div className="metric-value" style={{ color: '#ff4336' }}>{summary.critical}</div>
          <div className="metric-percentage">{criticalPercent}% of all issues</div>
        </div>
        
        <div className="metric-card" style={{ borderLeft: '4px solid #ffa500' }}>
          <div className="metric-label">HIGH Risk Issues</div>
          <div className="metric-value" style={{ color: '#ffa500' }}>{summary.high}</div>
          <div className="metric-percentage">{highPercent}% of all issues</div>
        </div>
        
        <div className="metric-card" style={{ borderLeft: '4px solid #ffc107' }}>
          <div className="metric-label">MEDIUM Risk Issues</div>
          <div className="metric-value" style={{ color: '#ffc107' }}>{summary.medium}</div>
          <div className="metric-percentage">{mediumPercent}% of all issues</div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid #00d4ff' }}>
          <div className="metric-label">Total Issues</div>
          <div className="metric-value" style={{ color: '#00d4ff' }}>{summary.total}</div>
          <div className="metric-percentage">Across 4 files</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '30px' }}>
        <h3 style={{ color: '#00d4ff', marginBottom: '20px' }}>Risks by File</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          {Object.entries(fileRisks).map(([filename, risks]) => (
            <div key={filename} style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <h4 style={{ color: '#00d4ff', marginBottom: '10px' }}>{filename}</h4>
              <div style={{ fontSize: '0.9em', color: '#a0a0a0' }}>
                <div style={{ marginBottom: '5px', color: '#ff4336' }}>🔴 Critical: {risks.critical}</div>
                <div style={{ marginBottom: '5px', color: '#ffa500' }}>🟠 High: {risks.high}</div>
                <div style={{ marginBottom: '5px', color: '#ffc107' }}>🟡 Medium: {risks.medium}</div>
                <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '10px', marginTop: '10px', color: '#e0e0e0', fontWeight: 'bold' }}>
                  Total: {risks.total}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 style={{ color: '#00d4ff', marginBottom: '15px' }}>Remediation Priority</h3>
        <div style={{ display: 'grid', gap: '15px' }}>
          <div style={{ background: 'rgba(255, 67, 54, 0.1)', padding: '15px', borderRadius: '8px', borderLeft: '4px solid #ff4336' }}>
            <div style={{ color: '#ff4336', fontWeight: 'bold', marginBottom: '5px' }}>Priority 1: CRITICAL Issues</div>
            <div style={{ color: '#a0a0a0', fontSize: '0.9em' }}>
              {summary.critical} issues must be fixed immediately before any deployment. These represent the highest security risk.
            </div>
          </div>
          
          <div style={{ background: 'rgba(255, 152, 0, 0.1)', padding: '15px', borderRadius: '8px', borderLeft: '4px solid #ffa500' }}>
            <div style={{ color: '#ffa500', fontWeight: 'bold', marginBottom: '5px' }}>Priority 2: HIGH Risk Issues</div>
            <div style={{ color: '#a0a0a0', fontSize: '0.9em' }}>
              {summary.high} issues should be addressed before production. Plan fixes for these in your next sprint.
            </div>
          </div>
          
          <div style={{ background: 'rgba(255, 193, 7, 0.1)', padding: '15px', borderRadius: '8px', borderLeft: '4px solid #ffc107' }}>
            <div style={{ color: '#ffc107', fontWeight: 'bold', marginBottom: '5px' }}>Priority 3: MEDIUM Issues</div>
            <div style={{ color: '#a0a0a0', fontSize: '0.9em' }}>
              {summary.medium} issues to consider. These can be addressed in future iterations or maintenance cycles.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MetricsPage
