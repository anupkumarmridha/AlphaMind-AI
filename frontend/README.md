# AlphaMind Frontend

React + Vite dashboard for the AlphaMind trading pipeline.

## Prerequisites

- Node.js 20+
- npm 10+

## Local Development

```bash
npm install
npm run dev
```

By default the app targets `http://localhost:8000`.

Set a custom backend URL:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Build and Lint

```bash
npm run lint
npm run build
```

## Data Model Notes

- `GET /dashboard` is the primary source for metrics, trades, decisions, and events.
- `POST /trade/run` triggers one full decision cycle and then dashboard data is refreshed.
- If the backend is unavailable, the UI falls back to mock data and shows `Data source: mock`.

