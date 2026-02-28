# HenShack Frontend

Next.js App Router frontend for the HenShack lift form analyzer.

## Setup

```bash
cd frontend
npm install

# Copy env example and adjust if needed
cp .env.local.example .env.local
```

## Development

```bash
# Start the backend first (in another terminal)
cd backend && uvicorn app.main:app --reload

# Start the frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | Backend API base URL (no trailing slash) |

## Project Structure

```
src/
├── app/
│   ├── globals.css      # Tailwind + custom CSS vars
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Single-page app (hero + input + results)
├── components/
│   ├── Recorder.tsx      # Webcam recording with MediaRecorder
│   ├── Uploader.tsx      # File upload with drag-and-drop
│   ├── ResultCard.tsx    # Analysis results display
│   ├── StatusPill.tsx    # Status badge component
│   └── VideoPlayer.tsx   # Simple video player wrapper
└── types/
    └── api.ts            # TypeScript types for API responses
```

## Features

- **Record mode**: Live webcam with start/stop, 60s hard cap, mm:ss timer
- **Upload mode**: Drag-and-drop or browse; validates max 50 MB / 60s duration
- **Lift selector**: Squat, bench, deadlift
- **Results**: Label badge, confidence %, score, AI feedback, issues with severity, annotated/comparison videos
- **Debug panel**: Collapsible raw JSON + frame/pose counts
- **Error handling**: Camera denied, MediaRecorder unsupported, file too large/long, backend errors, unknown label
