import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'https://ragify-uhkv.onrender.com'

export default function AuthPage({ setToken }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!status) return undefined

    const timer = window.setTimeout(() => {
      setStatus(null)
    }, 3000)

    return () => window.clearTimeout(timer)
  }, [status])

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setError(null)
    setStatus(null)
    setPassword('')
    setConfirmPassword('')
  }

  const submitAuth = async (e) => {
    e.preventDefault()
    setError(null)
    setStatus(null)
    setLoading(true)

    if (mode === 'signup' && password !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    if (mode === 'signup' && password.length < 6) {
      setError('Password must be at least 6 characters')
      setLoading(false)
      return
    }

    try {
      const res = await fetch(`${API_BASE}/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        const message = data.detail || data.message || `${mode} failed`
        throw new Error(mode === 'signup' && message.toLowerCase().includes('exists') ? 'Email already registered' : message)
      }
      const token = data.access_token || data.token || data.accessToken
      if (!token) throw new Error('No token in response')

      if (mode === 'signup') {
        setEmail('')
        setPassword('')
        setConfirmPassword('')
        setMode('login')
        setStatus('Account created. Please log in.')
        return
      }

      setToken(token)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <h2>{mode === 'login' ? 'Sign in' : 'Create Account'}</h2>
      <form onSubmit={submitAuth} className="auth-form">
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </label>
        {mode === 'signup' && (
          <label>
            Confirm Password
            <input value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} type="password" required />
          </label>
        )}
        <div className="form-actions">
          <button type="submit" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        {status && <div className="status">{status}</div>}
      </form>
      <div className="auth-toggle">
        <button
          type="button"
          className={`link-btn ${mode === 'login' ? 'active' : ''}`}
          onClick={() => switchMode('login')}
        >
          Login
        </button>
        <button
          type="button"
          className={`link-btn ${mode === 'signup' ? 'active' : ''}`}
          onClick={() => switchMode('signup')}
        >
          Create Account
        </button>
      </div>
    </div>
  )
}
