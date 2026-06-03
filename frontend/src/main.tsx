import React from 'react'
import ReactDOM from 'react-dom/client'
import { init } from '@telegram-apps/sdk'
import { HashRouter } from 'react-router-dom'
import App from './App.tsx'
import './index.css'

// Initialize the Telegram Mini App SDK before mounting React.
// Wrapped in try/catch so the app still renders in a plain browser (dev mode).
try {
  init()
} catch {
  // Running outside Telegram — SDK initialization is skipped
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>,
)
