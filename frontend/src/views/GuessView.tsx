import { useState, useEffect, useRef, useCallback } from 'react'
import './GuessView.css'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''

type ScoreColor = 'red' | 'orange' | 'yellow' | 'green' | 'gold'

interface GuessEntry {
  word: string
  score: number
  color: ScoreColor
}

function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? ''
}

function fireHaptic() {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
  } catch {
    // outside Telegram — ignore
  }
}

export default function GuessView() {
  const [word, setWord] = useState('')
  const [guesses, setGuesses] = useState<GuessEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const won = guesses.some(g => g.color === 'gold')
  const [highlightWord, setHighlightWord] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const initData = getInitData()
    if (!initData) return

    fetch(`${API_BASE}/guesses/today`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: initData }),
    })
      .then(r => (r.ok ? r.json() : Promise.resolve([])))
      .then((data: GuessEntry[]) => setGuesses(data))
      .catch(() => {})

    fetch(`${API_BASE}/register-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: initData }),
    }).catch(() => {})
  }, [])

  const markHighlight = useCallback((w: string) => {
    if (highlightTimer.current) clearTimeout(highlightTimer.current)
    setHighlightWord(w)
    highlightTimer.current = setTimeout(() => setHighlightWord(null), 2500)
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = word.trim().toLowerCase()
    if (!trimmed || loading) return

    const initData = getInitData()
    if (!initData) {
      setError('Відкрийте гру через Telegram')
      return
    }

    setLoading(true)
    setError(null)
    fireHaptic()

    try {
      const res = await fetch(`${API_BASE}/guess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: initData, word: trimmed }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setError((body as { detail?: string }).detail ?? 'Помилка сервера')
        return
      }

      const data = (await res.json()) as {
        score: number
        color: ScoreColor
        already_guessed: boolean
      }

      if (data.already_guessed) {
        markHighlight(trimmed)
      } else {
        setGuesses(prev =>
          [...prev, { word: trimmed, score: data.score, color: data.color }].sort(
            (a, b) => b.score - a.score,
          ),
        )
      }
    } catch {
      setError('Мережева помилка')
    } finally {
      setLoading(false)
      setWord('')
      inputRef.current?.focus()
    }
  }

  return (
    <div className="guess-view">
      <h1 className="guess-view__title">Семантле UA</h1>
      <p className="guess-view__hint">
        Вгадай секретне українське слово за семантичною схожістю.
        <br />
        Кожна спроба дає оцінку від 0 до 10 000.
      </p>

      {won && (
        <p className="guess-view__won">🎉 Ти знайшов слово! Повертайся завтра за новим.</p>
      )}

      {!won && (
        <form className="guess-view__input-row" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            className="guess-view__input"
            type="text"
            placeholder="Введи слово..."
            value={word}
            onChange={e => setWord(e.target.value)}
            disabled={loading}
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
          />
          <button
            type="submit"
            className="btn"
            style={{ width: 'auto', padding: '12px 20px' }}
            disabled={loading || !word.trim()}
          >
            →
          </button>
        </form>
      )}

      {error && <p className="guess-view__error">{error}</p>}

      {highlightWord && (
        <p className="guess-view__duplicate">
          «{highlightWord}» вже вгадано — дивись нижче
        </p>
      )}

      {guesses.length > 0 && (
        <ul className="guess-list">
          {guesses.map(g => (
            <li
              key={g.word}
              className={`guess-row guess-row--${g.color}${highlightWord === g.word ? ' guess-row--highlight' : ''}`}
            >
              <span className={`guess-row__dot guess-row__dot--${g.color}`} />
              <span className="guess-row__word">{g.word}</span>
              <span className="guess-row__score">{g.score.toLocaleString('uk-UA')}</span>
              {g.color === 'gold' && <span className="guess-row__trophy">🏆</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
