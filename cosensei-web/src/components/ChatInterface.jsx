import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import '../styles/ChatInterface.css'

// --------------------------------------------------------------------------- //
// Stable session IDs (persist across page refreshes)
// --------------------------------------------------------------------------- //
function getOrCreate(key, factory) {
  let val = localStorage.getItem(key)
  if (!val) { val = factory(); localStorage.setItem(key, val) }
  return val
}
const USER_ID = getOrCreate('cosensei_user_id',
  () => `user_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`)
const CHAT_ID = getOrCreate('cosensei_chat_id',
  () => `chat_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`)

// --------------------------------------------------------------------------- //
// Risk / Autonomy badge renderer
// --------------------------------------------------------------------------- //
const BADGE_MAP = {
  '[CRITICAL]': 'badge-critical', '[!!!]':       'badge-critical',
  '[HIGH]':     'badge-high',
  '[MED]':      'badge-med',      '[MEDIUM]':    'badge-med',
  '[LOW]':      'badge-low',      '[OK]':        'badge-ok',   '[FIXED]': 'badge-ok',
  '[NOTE]':     'badge-note',     '[INFO]':      'badge-note',
  '[AUTO_EXECUTE]':   'badge-auto',
  '[SHARED_CONTROL]': 'badge-shared',
  '[SUGGEST_ONLY]':   'badge-suggest',
  '[HUMAN_CONTROL]':  'badge-human',
  '[AUTO]':     'badge-auto',     '[SHARED]':    'badge-shared',
}

function renderInline(line) {
  const parts = []
  // Match **bold**, `code`, or [BADGE] tokens
  const re = /(\*\*(.+?)\*\*|`([^`]+)`|\[([A-Z_!]+)\])/g
  let last = 0, m
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) parts.push(line.slice(last, m.index))
    if (m[0].startsWith('**'))
      parts.push(<strong key={m.index}>{m[2]}</strong>)
    else if (m[0].startsWith('`'))
      parts.push(<code key={m.index} className="inline-code">{m[3]}</code>)
    else {
      const cls = BADGE_MAP[m[0]]
      if (cls)
        parts.push(<span key={m.index} className={`risk-badge ${cls}`}>{m[4]}</span>)
      else
        parts.push(m[0])
    }
    last = re.lastIndex
  }
  if (last < line.length) parts.push(line.slice(last))
  return parts.length ? parts : line
}

// --------------------------------------------------------------------------- //
// Table renderer  (lines that start and end with |)
// --------------------------------------------------------------------------- //
function TableBlock({ rows }) {
  if (!rows.length) return null
  const isHeader = (r) => r.every(c => /^[-: ]+$/.test(c.trim()))
  // find separator row
  const sepIdx = rows.findIndex(isHeader)
  const head = sepIdx > 0 ? rows.slice(0, sepIdx) : []
  const body = sepIdx >= 0 ? rows.slice(sepIdx + 1) : rows

  return (
    <div className="table-wrapper">
      <table className="data-table">
        {head.length > 0 && (
          <thead>
            {head.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <th key={ci}>{renderInline(cell.trim())}</th>
                ))}
              </tr>
            ))}
          </thead>
        )}
        <tbody>
          {body.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci}>{renderInline(cell.trim())}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function parseTableRow(line) {
  return line.replace(/^\||\|$/g, '').split('|')
}

function isTableLine(line) {
  return line.trim().startsWith('|') && line.trim().endsWith('|') && line.includes('|')
}

// --------------------------------------------------------------------------- //
// Markdown / code renderer
// --------------------------------------------------------------------------- //
function renderContent(text) {
  if (!text) return null

  // First split on fenced code blocks
  const codeBlockRe = /```(\w*)\n([\s\S]*?)```/g
  const segments = []
  let last = 0, match

  while ((match = codeBlockRe.exec(text)) !== null) {
    if (match.index > last) segments.push({ type: 'text', content: text.slice(last, match.index) })
    segments.push({ type: 'code', lang: match[1] || 'text', content: match[2] })
    last = codeBlockRe.lastIndex
  }
  if (last < text.length) segments.push({ type: 'text', content: text.slice(last) })

  return segments.map((seg, si) => {
    if (seg.type === 'code') {
      return (
        <div key={si} className="code-block-wrapper">
          <div className="code-block-header">
            <span className="code-lang">{seg.lang}</span>
            <button className="copy-btn" onClick={() => navigator.clipboard.writeText(seg.content)}>
              Copy
            </button>
          </div>
          <SyntaxHighlighter language={seg.lang} style={oneDark}
            customStyle={{ margin: 0, borderRadius: '0 0 6px 6px', fontSize: '0.82rem' }}>
            {seg.content}
          </SyntaxHighlighter>
        </div>
      )
    }

    // Parse text segment — may contain tables
    const lines = seg.content.split('\n')
    const out = []
    let tableRows = []
    let textBuf = []

    const flushText = () => {
      if (textBuf.length) {
        out.push(<InlineText key={`txt-${si}-${out.length}`} text={textBuf.join('\n')} />)
        textBuf = []
      }
    }
    const flushTable = () => {
      if (tableRows.length) {
        out.push(<TableBlock key={`tbl-${si}-${out.length}`} rows={tableRows} />)
        tableRows = []
      }
    }

    for (const line of lines) {
      if (isTableLine(line)) {
        flushText()
        tableRows.push(parseTableRow(line))
      } else {
        flushTable()
        textBuf.push(line)
      }
    }
    flushText()
    flushTable()
    return <React.Fragment key={si}>{out}</React.Fragment>
  })
}

// Renders prose: handles **bold**, inline `code`, ------ dividers, badges, line breaks
function InlineText({ text }) {
  const lines = text.split('\n')
  return (
    <div className="prose-block">
      {lines.map((line, i) => {
        if (/^={4,}$|^-{4,}$/.test(line.trim()))
          return <hr key={i} className="msg-hr" />

        // Callout lines — lines containing only a badge + content
        const calloutMatch = line.match(/^\s*(\[(?:CRITICAL|!!!|HIGH|MED|MEDIUM|LOW|OK|FIXED|NOTE|INFO|AUTO_EXECUTE|SHARED_CONTROL|SUGGEST_ONLY|HUMAN_CONTROL|AUTO|SHARED)\])\s*(.*)$/)
        if (calloutMatch) {
          const badgeCls = BADGE_MAP[calloutMatch[1]] || 'badge-note'
          return (
            <div key={i} className={`callout callout-${badgeCls.replace('badge-', '')}`}>
              <span className={`risk-badge ${badgeCls}`}>{calloutMatch[1].replace(/[\[\]]/g, '')}</span>
              {' '}
              <span>{renderInline(calloutMatch[2])}</span>
              {i < lines.length - 1 && null}
            </div>
          )
        }

        const rendered = renderInline(line)
        return (
          <React.Fragment key={i}>
            <span className={isSectionHeader(line) ? 'section-header' : ''}>{rendered}</span>
            {i < lines.length - 1 && <br />}
          </React.Fragment>
        )
      })}
    </div>
  )
}

function isSectionHeader(line) {
  const t = line.trim()
  return t.length > 2 && t.length < 60 && t === t.toUpperCase() && /[A-Z]/.test(t)
}

// --------------------------------------------------------------------------- //
// Main component
// --------------------------------------------------------------------------- //
export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const [online,   setOnline]   = useState(null)   // null=checking, true, false
  const endRef    = useRef(null)
  const inputRef  = useRef(null)

  // Auto-scroll
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  // Check backend health on mount
  useEffect(() => {
    fetch('/health').then(r => {
      setOnline(r.ok)
      if (!r.ok) addBotMsg("Backend is offline. Make sure the Flask server is running on port 5000.")
    }).catch(() => {
      setOnline(false)
      addBotMsg("Cannot reach backend. Start it with:\n\n```bash\ncd terminal_stress_ai && .venv/Scripts/python.exe app/risk_api_server.py\n```")
    })
  }, [])

  const addBotMsg = (content) => {
    setMessages(prev => [...prev, {
      role: 'assistant', content,
      id: Date.now() + Math.random()
    }])
  }

  const send = useCallback(async (text) => {
    const msg = text.trim()
    if (!msg || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg, id: Date.now() }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ message: msg, chat_id: CHAT_ID, user_id: USER_ID }),
      })

      if (res.ok) {
        const data = await res.json()
        const content = data.message || data.response || '(empty response)'
        setMessages(prev => [...prev, { role: 'assistant', content, id: Date.now() }])
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Server error ${res.status}. Check the backend terminal for details.`,
          id: Date.now()
        }])
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Could not reach the backend. Is it running?',
        id: Date.now()
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [loading])

  const handleSubmit = (e) => { e.preventDefault(); send(input) }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) }
  }

  // New session button
  const startNew = () => {
    localStorage.removeItem('cosensei_chat_id')
    // Generate fresh chat id for next send
    const newId = `chat_${Date.now()}_${Math.random().toString(36).slice(2,9)}`
    localStorage.setItem('cosensei_chat_id', newId)
    // Reload the page so constants reinitialize
    window.location.reload()
  }

  return (
    <div className="chat-root">
      {/* ── Header ── */}
      <header className="chat-header">
        <div className="header-left">
          <span className="header-logo">COSENSEI</span>
          <span className={`status-dot ${online === true ? 'online' : online === false ? 'offline' : 'checking'}`} />
          <span className="status-label">
            {online === true ? 'ONLINE' : online === false ? 'OFFLINE' : 'CONNECTING...'}
          </span>
        </div>
        <div className="header-right">
          <span className="session-id">SESSION: {CHAT_ID.slice(-8).toUpperCase()}</span>
          <button className="new-session-btn" onClick={startNew}>New Session</button>
        </div>
      </header>

      {/* ── Messages ── */}
      <div className="chat-messages">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <div className="empty-icon">CS</div>
            <p>CoSensei is ready. Tell me what you want to build.</p>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`msg-row ${msg.role}`}>
            <div className="msg-avatar">{msg.role === 'user' ? 'OP' : 'CS'}</div>
            <div className="msg-bubble">
              <div className="msg-body">
                {renderContent(msg.content)}
              </div>
              <span className="msg-time">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="msg-row assistant">
            <div className="msg-avatar">CS</div>
            <div className="msg-bubble">
              <div className="typing-dots"><span/><span/><span/></div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* ── Input ── */}
      <form className="chat-input-row" onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          className="chat-textarea"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type your message… (Enter to send, Shift+Enter for new line)"
          disabled={loading}
          rows={1}
        />
        <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
          {loading ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
