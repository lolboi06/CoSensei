import React from 'react'

function SecuritySummary({ summary }) {
  return (
    <div className="stats-section" style={{ marginBottom: '30px' }}>
      <div className="stat-card" style={{ borderLeft: '4px solid #ff4336' }}>
        <div className="stat-number" style={{ color: '#ff4336' }}>
          {summary.critical}
        </div>
        <div className="stat-label">CRITICAL Issues</div>
        <p style={{ color: '#ff6b6b', fontSize: '0.8em', marginTop: '8px' }}>
          Must fix before deployment
        </p>
      </div>
      
      <div className="stat-card" style={{ borderLeft: '4px solid #ffa500' }}>
        <div className="stat-number" style={{ color: '#ffa500' }}>
          {summary.high}
        </div>
        <div className="stat-label">HIGH Risk Issues</div>
        <p style={{ color: '#ffb74d', fontSize: '0.8em', marginTop: '8px' }}>
          Should fix before deployment
        </p>
      </div>
      
      <div className="stat-card" style={{ borderLeft: '4px solid #ffc107' }}>
        <div className="stat-number" style={{ color: '#ffc107' }}>
          {summary.medium}
        </div>
        <div className="stat-label">MEDIUM Risk Issues</div>
        <p style={{ color: '#ffd54f', fontSize: '0.8em', marginTop: '8px' }}>
          Consider fixing in next iteration
        </p>
      </div>
    </div>
  )
}

export default SecuritySummary
