# Semantle UA — Frontend

## Overview

The frontend is a Telegram Mini App built with React + Vite (TypeScript), deployed to Cloudflare Pages. It is a pure client-side SPA — no server-side rendering. The app runs inside Telegram's WebView and communicates with the backend FastAPI service.

---

## Tech Stack

| Concern | Technology |
|---------|-----------|
| Framework | React 18 |
| Bundler | Vite 5 |
| Language | TypeScript 5 |
| Routing | React Router v6 (HashRouter) |
| Telegram SDK | `@telegram-apps/sdk` v3 + `@telegram-apps/sdk-react` v3 |
| Hosting | Cloudflare Pages |
| Deployment config | `wrangler.toml` (`pages_build_output_dir = "dist"`) |

---

## Directory Layout

```
frontend/
├── src/
│   ├── main.tsx              # Entry point: SDK init, React mount
│   ├── App.tsx               # Root component: SDK hooks, router outlet
│   ├── index.css             # Global styles + Telegram CSS var mappings
│   ├── telegram.d.ts         # Type declarations for window.Telegram.WebApp
│   ├── components/
│   │   ├── Navigation.tsx    # Tab bar: Guess / Leaderboard
│   │   └── Navigation.css
│   └── views/
│       ├── GuessView.tsx     # Guess input placeholder
│       ├── GuessView.css
│       ├── LeaderboardView.tsx  # Leaderboard placeholder
│       └── LeaderboardView.css
├── index.html                # HTML shell + telegram-web-app.js script tag
├── package.json
├── tsconfig.json             # Project references root
├── tsconfig.app.json         # App source compiler options
├── tsconfig.node.json        # vite.config.ts compiler options
├── vite.config.ts
├── wrangler.toml             # Cloudflare Pages deployment config
└── .gitignore
```

---

## SDK Initialization

`@telegram-apps/sdk` v3 uses an explicit mount model. Initialization runs before React mounts:

```
main.tsx        init()                       ← registers SDK with Telegram bridge
App.tsx effect  mountMiniAppSync()           ← mounts MiniApp component
                mountThemeParamsSync()       ← mounts ThemeParams component
                bindThemeParamsCssVars()     ← writes --tg-theme-* CSS vars to <html>
                miniAppReady()               ← tells Telegram to reveal the WebView
```

All calls are guarded with `.isAvailable()` (v3 safe-wrap pattern) and wrapped in `try/catch` so the app still renders in a plain browser during local development.

---

## Telegram Theme Integration

`bindThemeParamsCssVars()` writes Telegram's theme colors to CSS custom properties on the `<html>` element. These are also injected automatically by the `telegram-web-app.js` script in `index.html`. The app's `index.css` maps them to internal design tokens:

```css
:root {
  --color-bg:          var(--tg-theme-bg-color, #ffffff);
  --color-text:        var(--tg-theme-text-color, #000000);
  --color-hint:        var(--tg-theme-hint-color, #708499);
  --color-button:      var(--tg-theme-button-color, #2678b6);
  --color-button-text: var(--tg-theme-button-text-color, #ffffff);
  /* ...etc */
}
```

All components consume `--color-*` tokens, not raw Telegram vars. Light-mode fallback values keep the app usable outside Telegram.

---

## Routing

`HashRouter` is used (URL hash-based) to avoid needing server-side redirect rules on Cloudflare Pages. Two routes are defined:

| Path | View | Purpose |
|------|------|---------|
| `/#/guess` | `GuessView` | Daily word guessing (game logic TBD) |
| `/#/leaderboard` | `LeaderboardView` | Group leaderboard (API integration TBD) |

`/` redirects to `/#/guess`.

---

## Cloudflare Pages Deployment

`wrangler.toml` at `frontend/wrangler.toml`:

```toml
name = "semantle-ua"
pages_build_output_dir = "dist"
compatibility_date = "2025-01-01"
```

Deploy via:

```bash
cd frontend
npm run build
npx wrangler pages deploy dist
```

Or connect the `frontend/` directory to a Cloudflare Pages project in the dashboard, with build command `npm run build` and output directory `dist`.

---

## Local Development

```bash
cd frontend
npm install
npm run dev        # Vite dev server at http://localhost:5173
npm run build      # Production build → dist/
npm run preview    # Preview production build locally
```

Running outside Telegram is fine — the SDK init is skipped gracefully, and CSS fallback values keep the UI visible.

---

## Score Color Palette

Defined in `index.css` for future use in `GuessView`:

| Score range | CSS var | Color |
|-------------|---------|-------|
| 0–2,000 | `--score-red` | `#e53e3e` |
| 2,001–5,000 | `--score-orange` | `#dd6b20` |
| 5,001–7,500 | `--score-yellow` | `#d69e2e` |
| 7,501–9,999 | `--score-green` | `#38a169` |
| 10,000 | `--score-gold` | `#b7791f` |

---

## What's Not Yet Implemented (Next Issues)

- Guess submission logic + score display
- History list (sorted by score, color-coded)
- Leaderboard API integration
- Duplicate guess detection (returns stored score)
- `initData` forwarded to backend on every API call
- Real-time leaderboard updates
