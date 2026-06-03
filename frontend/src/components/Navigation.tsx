import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import './Navigation.css'

function detectChatId(): boolean {
  const initData = window.Telegram?.WebApp?.initData ?? ''
  if (!initData) return false
  return new URLSearchParams(initData).has('chat')
}

export default function Navigation() {
  const [showLeaderboard] = useState(detectChatId)

  return (
    <nav className="nav">
      <NavLink to="/guess" className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>
        Вгадати
      </NavLink>
      {showLeaderboard && (
        <NavLink to="/leaderboard" className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>
          Рейтинг
        </NavLink>
      )}
    </nav>
  )
}
