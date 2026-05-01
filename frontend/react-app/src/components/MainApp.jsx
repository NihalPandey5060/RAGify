import React, { useEffect, useState, useRef } from 'react'

const TOKEN_KEY = 'token'
const API_BASE = 'https://your-backend-name.onrender.com'

export default function MainApp({ token, setToken }) {
  const [user, setUser] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadStatus, setUploadStatus] = useState(null)

  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([]) // {role:'assistant'|'user', text}
  const [isStreaming, setIsStreaming] = useState(false)
  const [retrievals, setRetrievals] = useState([])
  const decoderRef = useRef(new TextDecoder())

  useEffect(() => {
    let mounted = true
    async function fetchMe() {
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error('Failed to fetch user')
        const data = await res.json()
        if (mounted) setUser(data)
      } catch (err) {
        console.error(err)
      }
    }
    fetchMe()
    return () => {
      mounted = false
    }
  }, [token])

  const logout = () => {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {}
    setToken(null)
  }

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files?.[0] || null)
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return setUploadStatus('No file selected')
    setUploadStatus('Uploading...')
    const fd = new FormData()
    fd.append('file', selectedFile)
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || 'Upload failed')
      setUploadStatus('Uploaded')
    } catch (err) {
      setUploadStatus(err.message)
    }
  }

  const appendMessage = (msg) => setMessages((m) => [...m, msg])

  const sendQuestionStreaming = async (e) => {
    e?.preventDefault()
    if (!question) return
    appendMessage({ role: 'user', text: question })
    setIsStreaming(true)
    setRetrievals([])
    appendMessage({ role: 'assistant', text: '' })
    try {
      const res = await fetch(`${API_BASE}/query/ask-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: question }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || err.message || 'Query failed')
      }

      const reader = res.body.getReader()
      let buffer = ''
      const decoder = decoderRef.current

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          if (!part.trim()) continue
          let ev
          try {
            ev = JSON.parse(part)
          } catch (err) {
            console.warn('non-json chunk', part)
            continue
          }
          if (ev.type === 'answer_chunk') {
            // append to last assistant message
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              const rest = prev.slice(0, -1)
              const updated = { ...last, text: (last?.text || '') + (ev.content || '') }
              return [...rest, updated]
            })
          } else if (ev.type === 'retrieval_complete') {
            setRetrievals((r) => [...r, ev])
          } else if (ev.type === 'complete') {
            // finalization
          }
        }
      }
    } catch (err) {
      appendMessage({ role: 'assistant', text: `Error: ${err.message}` })
    } finally {
      setIsStreaming(false)
      setQuestion('')
    }
  }

  return (
    <div className="main-app">
      <header className="app-header">
        <div className="brand">RAG App</div>
        <div className="user-area">
          {user && <span className="user-email">{user.email}</span>}
          <button className="logout-btn" onClick={logout}>Logout</button>
        </div>
      </header>

      <main style={{ padding: 16 }}>
        <section style={{ marginBottom: 20 }}>
          <h3>Upload Document</h3>
          <form onSubmit={handleUpload}>
            <input type="file" onChange={handleFileChange} />
            <button type="submit">Upload</button>
          </form>
          {uploadStatus && <div style={{ marginTop: 8 }}>{uploadStatus}</div>}
        </section>

        <section style={{ marginBottom: 20 }}>
          <h3>Chat (streaming)</h3>
          <form onSubmit={sendQuestionStreaming} style={{ display: 'flex', gap: 8 }}>
            <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question..." style={{ flex: 1 }} />
            <button type="submit" disabled={isStreaming}>{isStreaming ? 'Streaming...' : 'Ask'}</button>
          </form>

          <div style={{ marginTop: 12 }}>
            {messages.map((m, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <strong>{m.role === 'user' ? 'You' : 'Assistant'}:</strong>
                <div>{m.text}</div>
              </div>
            ))}
          </div>

          {retrievals.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <h4>Retrievals</h4>
              <ul>
                {retrievals.map((r, idx) => (
                  <li key={idx}>{r.source || r.text || JSON.stringify(r)}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
