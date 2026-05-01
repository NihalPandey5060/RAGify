import React, { useEffect, useState } from 'react'
import AuthPage from './components/AuthPage'
import MainApp from './components/MainApp'

const TOKEN_KEY = 'token'

export default function App() {
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  })

  useEffect(() => {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token)
      else localStorage.removeItem(TOKEN_KEY)
    } catch {}
  }, [token])

  return token ? (
    <MainApp token={token} setToken={setToken} />
  ) : (
    <AuthPage setToken={setToken} />
  )
}
