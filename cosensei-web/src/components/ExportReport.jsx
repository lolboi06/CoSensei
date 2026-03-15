import React from 'react'

function ExportReport({ fileData, summary }) {
  const generateTextReport = () => {
    let report = '======================================================================\n'
    report += 'COSENSEI - SECURITY RISK ANALYSIS REPORT\n'
    report += '======================================================================\n\n'
    report += `Generated: ${new Date().toLocaleString()}\n\n`
    
    report += 'EXECUTIVE SUMMARY\n'
    report += '======================================================================\n'
    report += `Total Vulnerabilities: ${summary.total}\n`
    report += `  - CRITICAL: ${summary.critical} (Must fix before deployment)\n`
    report += `  - HIGH: ${summary.high} (Should fix before deployment)\n`
    report += `  - MEDIUM: ${summary.medium} (Consider fixing)\n\n`
    
    report += 'FILES ANALYZED\n'
    report += '======================================================================\n'
    Object.entries(fileData).forEach(([filename, data]) => {
      report += `\n${filename.toUpperCase()}\n`
      report += `Title: ${data.title}\n`
      report += `Description: ${data.description}\n`
      report += `Risks Found: ${data.risks.length}\n\n`
      
      report += 'VULNERABILITIES:\n'
      data.risks.forEach((risk, idx) => {
        report += `  ${idx + 1}. [${risk.severity}] ${risk.title}\n`
        report += `     ${risk.description}\n\n`
      })
      
      report += 'RECOMMENDED FIXES:\n'
      data.fixes.forEach((fix, idx) => {
        report += `  ${idx + 1}. ${fix}\n`
      })
      report += '\n' + '----------------------------------------------------------------------\n'
    })
    
    report += '\n\nNEXT STEPS\n'
    report += '======================================================================\n'
    report += '1. Review all CRITICAL vulnerabilities first\n'
    report += '2. Implement recommended fixes for each vulnerability\n'
    report += '3. Update code with secure versions provided\n'
    report += '4. Re-run security analysis to verify fixes\n'
    report += '5. Deploy to production with confidence\n\n'
    report += 'For more information, visit: http://localhost:3000\n'
    
    return report
  }

  const downloadReport = () => {
    const report = generateTextReport()
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(report))
    element.setAttribute('download', `cosensei-security-report-${new Date().toISOString().slice(0, 10)}.txt`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const copyReport = async () => {
    const report = generateTextReport()
    try {
      await navigator.clipboard.writeText(report)
      alert('Report copied to clipboard!')
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="export-section">
      <h3 style={{ marginBottom: '15px', color: '#00d4ff' }}>📊 Export Analysis</h3>
      <p style={{ color: '#a0a0a0', marginBottom: '15px' }}>
        Generate a detailed security analysis report
      </p>
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <button onClick={downloadReport} style={{ background: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)' }}>
          📥 Download Report
        </button>
        <button onClick={copyReport} style={{ background: 'rgba(0, 212, 255, 0.2)', color: '#00d4ff', border: '1px solid rgba(0, 212, 255, 0.4)' }}>
          📋 Copy to Clipboard
        </button>
      </div>
    </div>
  )
}

export default ExportReport
