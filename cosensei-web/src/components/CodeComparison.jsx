import React, { useState } from 'react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { atom } from 'react-syntax-highlighter/dist/esm/styles/hljs'

function CodeComparison({ fileData }) {
  const [showSecure, setShowSecure] = useState(false)
  const [copiedUnsafe, setCopiedUnsafe] = useState(false)
  const [copiedSecure, setCopiedSecure] = useState(false)

  const copyToClipboard = (code, isSecure) => {
    navigator.clipboard.writeText(code)
    if (isSecure) {
      setCopiedSecure(true)
      setTimeout(() => setCopiedSecure(false), 2000)
    } else {
      setCopiedUnsafe(true)
      setTimeout(() => setCopiedUnsafe(false), 2000)
    }
  }

  const unsafeCode = fileData.unsafeCode
  const secureCode = fileData.secureCode

  return (
    <div className="card" style={{ marginBottom: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
        <h3 style={{ color: '#00d4ff' }}>Code Comparison</h3>
        <button onClick={() => setShowSecure(!showSecure)}>
          {showSecure ? '← Back to Unsafe' : 'Compare with Secure →'}
        </button>
      </div>

      {!showSecure ? (
        // Unsafe Code View
        <div>
          <div className="code-header">
            <span className="code-label">❌ Unsafe Code (Current)</span>
            <button 
              className={`copy-btn ${copiedUnsafe ? 'copied' : ''}`}
              onClick={() => copyToClipboard(unsafeCode, false)}
            >
              {copiedUnsafe ? '✓ Copied' : 'Copy'}
            </button>
          </div>
          <div className="code-block unsafe-code" style={{ padding: 0, background: 'transparent', border: 'none' }}>
            <SyntaxHighlighter 
              language="python" 
              style={atom}
              customStyle={{
                background: 'rgba(255, 67, 54, 0.1)',
                border: '1px solid rgba(255, 67, 54, 0.3)',
                borderRadius: '8px',
                padding: '15px',
              }}
            >
              {unsafeCode}
            </SyntaxHighlighter>
          </div>
        </div>
      ) : (
        // Secure Code View
        <div>
          <div className="code-header">
            <span className="code-label">✓ Secure Code (Recommended)</span>
            <button 
              className={`copy-btn ${copiedSecure ? 'copied' : ''}`}
              onClick={() => copyToClipboard(secureCode, true)}
            >
              {copiedSecure ? '✓ Copied' : 'Copy'}
            </button>
          </div>
          <div className="code-block secure-code" style={{ padding: 0, background: 'transparent', border: 'none' }}>
            <SyntaxHighlighter 
              language="python" 
              style={atom}
              customStyle={{
                background: 'rgba(76, 175, 80, 0.1)',
                border: '1px solid rgba(76, 175, 80, 0.3)',
                borderRadius: '8px',
                padding: '15px',
              }}
            >
              {secureCode}
            </SyntaxHighlighter>
          </div>
        </div>
      )}

      <div style={{ marginTop: '20px' }}>
        <h4 style={{ marginBottom: '10px', color: '#a0d000' }}>🔧 How to Fix These Issues</h4>
        <ul className="fix-list">
          {fileData.fixes.map((fix, idx) => (
            <li key={idx}>{fix}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default CodeComparison

