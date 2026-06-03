import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import {
  mountMiniAppSync,
  mountThemeParamsSync,
  bindThemeParamsCssVars,
  miniAppReady,
} from '@telegram-apps/sdk'
import GuessView from './views/GuessView'
import LeaderboardView from './views/LeaderboardView'
import Navigation from './components/Navigation'

function useTelegramInit() {
  useEffect(() => {
    try {
      if (mountMiniAppSync.isAvailable()) mountMiniAppSync()
      if (mountThemeParamsSync.isAvailable()) mountThemeParamsSync()
      if (bindThemeParamsCssVars.isAvailable()) bindThemeParamsCssVars()
      if (miniAppReady.isAvailable()) miniAppReady()
    } catch {
      // Outside Telegram — skipped
    }
  }, [])
}

export default function App() {
  useTelegramInit()

  return (
    <div className="app">
      <Navigation />
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/guess" replace />} />
          <Route path="/guess" element={<GuessView />} />
          <Route path="/leaderboard" element={<LeaderboardView />} />
        </Routes>
      </main>
    </div>
  )
}
