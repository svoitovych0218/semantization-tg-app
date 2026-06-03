import { NavLink } from 'react-router-dom'
import './Navigation.css'

export default function Navigation() {
  return (
    <nav className="nav">
      <NavLink to="/guess" className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>
        Вгадати
      </NavLink>
      <NavLink to="/leaderboard" className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>
        Рейтинг
      </NavLink>
    </nav>
  )
}
