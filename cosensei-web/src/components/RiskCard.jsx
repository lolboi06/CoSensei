import React from 'react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { atom } from 'react-syntax-highlighter/dist/esm/styles/hljs'

function RiskCard({ fileData }) {
  const getRiskColor = (severity) => {
    if (severity === 'CRITICAL') return 'risk-critical'
    if (severity === 'HIGH') return 'risk-high'
    return 'risk-medium'
  }

  const getSeverityIndicator = (severity) => {
    if (severity === 'CRITICAL') return '🔴'
    if (severity === 'HIGH') return '🟠'
    return '🟡'
  }

  return (
    <div className="card" style={{ marginBottom: '30px' }}>
      <h2>{fileData.title}</h2>
      <p style={{ color: '#a0a0a0', marginBottom: '20px' }}>{fileData.description}</p>
      
      <h3 style={{ marginBottom: '15px', color: '#00d4ff' }}>Identified Vulnerabilities</h3>
      <div>
        {fileData.risks.map((risk, idx) => (
          <div key={idx} style={{ marginBottom: '20px', paddingBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span>{getSeverityIndicator(risk.severity)}</span>
              <span className={`risk-badge ${getRiskColor(risk.severity)}`}>
                [{risk.severity}]
              </span>
            </div>
            <h4 style={{ color: '#e0e0e0', marginBottom: '8px' }}>{risk.title}</h4>
            <p style={{ color: '#a0a0a0', marginBottom: '10px' }}>{risk.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RiskCard

