import { useState, useEffect, useCallback } from 'react'
import './LeaderboardView.css'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''

type ScoreColor = 'red' | 'orange' | 'yellow' | 'green' | 'gold'

interface LeaderboardEntry {
  user_id: number
  first_name: string
  best_score: number
  is_winner: boolean
}

function parseInitData(): { chatId?: number; userId?: number } {
  const initData = window.Telegram?.WebApp?.initData ?? ''
  if (!initData) return {}
  const params = new URLSearchParams(initData)
  let chatId: number | undefined
  let userId: number | undefined

  const chatStr = params.get('chat')
  if (chatStr) {
    try { chatId = JSON.parse(chatStr).id } catch {}
  }

  const userStr = params.get('user')
  if (userStr) {
    try { userId = JSON.parse(userStr).id } catch {}
  }

  return { chatId, userId }
}

function scoreToColor(score: number): ScoreColor {
  if (score === 10000) return 'gold'
  if (score >= 7501) return 'green'
  if (score >= 5001) return 'yellow'
  if (score >= 2001) return 'orange'
  return 'red'
}

function todayIso(): string {
  return new Date().toISOString().split('T')[0]
}

export default function LeaderboardView() {
  const [{ chatId, userId }] = useState(parseInitData)
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLeaderboard = useCallback(async () => {
    if (!chatId) return
    try {
      const res = await fetch(`${API_BASE}/leaderboard?chat_id=${chatId}&date=${todayIso()}`)
      if (!res.ok) {
        setError('Не вдалося завантажити рейтинг')
        return
      }
      setEntries(await res.json())
      setError(null)
    } catch {
      setError('Мережева помилка')
    } finally {
      setLoading(false)
    }
  }, [chatId])

  useEffect(() => {
    fetchLeaderboard()
    const id = setInterval(fetchLeaderboard, 10_000)
    return () => clearInterval(id)
  }, [fetchLeaderboard])

  if (!chatId) return null

  return (
    <div className="leaderboard-view">
      <h1 className="leaderboard-view__title">Рейтинг</h1>
      <p className="leaderboard-view__hint">
        Рейтинг гравців цього чату за сьогодні.
      </p>

      {loading ? (
        <p className="leaderboard-view__hint leaderboard-view__loading">Завантаження…</p>
      ) : error ? (
        <p className="leaderboard-view__error">{error}</p>
      ) : entries.length === 0 ? (
        <div className="leaderboard-view__empty">
          <span className="leaderboard-view__empty-icon">🏆</span>
          <p>Ще ніхто не вгадував сьогодні.</p>
          <p className="leaderboard-view__empty-sub">Будь першим!</p>
        </div>
      ) : (
        <ol className="lb-list">
          {entries.map((entry, idx) => {
            const color = scoreToColor(entry.best_score)
            const isMe = entry.user_id === userId
            return (
              <li key={entry.user_id} className={`lb-row${isMe ? ' lb-row--me' : ''}`}>
                <span className="lb-row__rank">#{idx + 1}</span>
                <span className={`lb-row__dot lb-row__dot--${color}`} />
                <span className="lb-row__name">
                  {entry.first_name}
                  {isMe && <span className="lb-row__you"> (ти)</span>}
                </span>
                <span className={`lb-row__score lb-row__score--${color}`}>
                  {entry.best_score.toLocaleString('uk-UA')}
                </span>
                {entry.is_winner && <span className="lb-row__trophy">🏆</span>}
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
