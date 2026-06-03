import './LeaderboardView.css'

export default function LeaderboardView() {
  return (
    <div className="leaderboard-view">
      <h1 className="leaderboard-view__title">Рейтинг</h1>
      <p className="leaderboard-view__hint">
        Рейтинг гравців цього чату за сьогодні.
      </p>

      <div className="leaderboard-view__empty">
        <span className="leaderboard-view__empty-icon">🏆</span>
        <p>Ще ніхто не вгадував сьогодні.</p>
        <p className="leaderboard-view__empty-sub">Будь першим!</p>
      </div>

      <p className="leaderboard-view__placeholder">
        Рейтинг буде підключено до API у наступних ітераціях.
      </p>
    </div>
  )
}
