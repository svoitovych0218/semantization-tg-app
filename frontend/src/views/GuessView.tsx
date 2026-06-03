import './GuessView.css'

export default function GuessView() {
  return (
    <div className="guess-view">
      <h1 className="guess-view__title">Семантле UA</h1>
      <p className="guess-view__hint">
        Вгадай секретне українське слово за семантичною схожістю.
        <br />
        Кожна спроба дає оцінку від 0 до 10 000.
      </p>

      <div className="guess-view__input-row">
        <input
          className="guess-view__input"
          type="text"
          placeholder="Введи слово..."
          disabled
        />
        <button className="btn" style={{ width: 'auto', padding: '12px 20px' }} disabled>
          →
        </button>
      </div>

      <p className="guess-view__placeholder">
        Ігрова логіка буде додана у наступних ітераціях.
      </p>
    </div>
  )
}
