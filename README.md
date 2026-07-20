# Signal Sync

Signal Sync is a combined Python + Next.js application for BGV, financial analysis, and investor recommendation workflows.

The repository has two main runnable parts:

- A Python API in `src/` that serves the investor recommendation endpoint and the BGV pipeline.
- A Next.js frontend in `frontend/ui/` that calls the Python API and uses Supabase for profile storage.

## Project Layout

```
signal_sync/
├── src/                      # Python API and agentic pipeline
├── frontend/ui/              # Next.js frontend
├── streamlit_app/            # Optional Streamlit UI
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Python package metadata
└── .env.example              # Example backend environment file
```

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- npm

## Environment Variables

Create a root `.env` file for the Python side. The code reads this file automatically.

Required or commonly used variables:

- `OPENAI_API_KEY` for the agentic analysis and recommendation stack
- `SERPER_API_KEY` for web search support where used
- `NEWSDATA_API_KEY` for the news tool if you use the financial analysis agents
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD`, `REDDIT_USER_AGENT` for the reddit sentiment module if you use it

For the frontend, create `frontend/ui/.env.local` with:

- `NEXT_PUBLIC_BGV_API_BASE_URL=http://localhost:8000`
- `NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<your-supabase-anon-or-publishable-key>`
- `NEXT_PUBLIC_SITE_URL=http://localhost:3000`

## Setup

### 1) Clone the repository

```bash
cd signal_sync
```

### 2) Set up the Python environment

From the repository root:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install fastapi "uvicorn[standard]" python-multipart aiofiles
```

The root `requirements.txt` mirrors the project stack, but the editable install above is the safest fresh-machine setup because it avoids the duplicate pin conflict in that file.

### 3) Set up the frontend

Open a second terminal and go to the Next.js app:

```bash
cd frontend/ui
npm install
```

If you already have the lockfile dependencies installed, `npm i` is also fine.

## Running the App

Run the Python API first, then start the frontend.

### Backend API

From the repository root, with the virtual environment active:

```bash
python -m uvicorn src.api.bgv_api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- `http://localhost:8000`
- `http://localhost:8000/docs` for the FastAPI Swagger UI

### Frontend UI

From `frontend/ui`:

```bash
npm run dev
```

The frontend will run on:

- `http://localhost:3000`

## Recommended Local Startup Order

1. Activate the Python virtual environment.
2. Start the Python API with `python -m uvicorn src.api.bgv_api:app --reload --host 0.0.0.0 --port 8000`.
3. In a second terminal, go to `frontend/ui`.
4. Install frontend dependencies with `npm install` if needed.
5. Start the frontend with `npm run dev`.

## Notes

- The investor recommendation page expects Supabase tables and env vars to be configured before you try to persist recommendations.
- If the frontend cannot reach the backend, verify `NEXT_PUBLIC_BGV_API_BASE_URL` points to `http://localhost:8000`.
- If you are only testing the Python API, you can use FastAPI at `/docs` without starting the frontend.

## Optional Streamlit App

If you want the legacy Streamlit interface, run:

```bash
streamlit run streamlit_app/app.py
```

## Disclaimer

This project is for informational purposes only. It is not financial advice, and outputs should be reviewed with your own due diligence.
