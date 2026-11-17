# EmergencyRoute AI — Production Deployment & Security Guide

This document details the production deployment architecture, security hardening, and zero-key-exposure model implemented in **EmergencyRoute AI**.

---

## 1. Zero-Key-Exposure Security Architecture

```
[ Client Browser ]
        │  (No API keys stored in localStorage, sessionStorage, or JavaScript bundles)
        │  Requests: /api/v1/traffic/...
        ▼
[ FastAPI Backend Gateway ]
        │  1. Loads TOMTOM_API_KEY / DELHIVERY_API_KEY from server environment (.env or OS ENV)
        │  2. Automatically redacts keys from all logs, exceptions, and traces
        │  3. Injects server credentials to upstream APIs securely
        ▼
[ External Telemetry Providers ] (TomTom / OSRM / OpenStreetMap)
```

### Key Security Safeguards
1. **Zero Client Bundling:** Neither `VITE_` prefix nor raw strings of any third-party API key exist in `frontend/dist/`.
2. **Reverse Proxy Architecture:** Traffic tiles (`/api/v1/traffic/tiles/...`), flow segments (`/api/v1/traffic/flow-segment`), and accident hazard feeds (`/api/v1/traffic/incident-details`) are proxied server-side.
3. **Telemetry Status Obfuscation:** The status endpoint (`/api/v1/traffic/telemetry-status`) returns boolean operational flags (`{"configured": true}`) without revealing even a single character or hash of the actual credential.
4. **Log Redaction:** All error messages and HTTP logs pass through regex masking filters (`redact_sensitive`) ensuring Bearer tokens and `key=...` values are sanitized before reaching stdout or disk logs.
5. **Airtight `.gitignore` Protection:**
   - Blocks `.env`, `.env.*`, `*.key`, `*.pem`, `*.cert`, `*.secret`, `*.token`, `*credentials*.json`, and `secrets*.json`.
   - Only `.env.example` (with empty template values) is tracked by git.

---

## 2. Deployment Options

### Option A: Docker / Docker Compose (Recommended for Cloud & VPS)

The project includes an optimized multi-stage `Dockerfile` and `docker-compose.yml`:
- **Stage 1 (Frontend Builder):** Compiles the React + Vite frontend into optimized static files with `node:20-alpine`.
- **Stage 2 (Runtime):** Packages the FastAPI application, authoritative Phagwara road graph, and production static assets into a slim `python:3.10-slim` container.

#### Single-Command Launch:
```bash
# 1. Ensure your server .env contains your private keys (never committed to git)
cp .env.example .env
# Edit .env with your TOMTOM_API_KEY

# 2. Build and run container
docker-compose up -d --build
```
Access the application at:
- **Application UI:** `http://your-server-ip:8000/`
- **Interactive Swagger Docs:** `http://your-server-ip:8000/docs`
- **Health Check:** `http://your-server-ip:8000/api/v1/health`

---

### Option B: Local / Bare-Metal Production Runner (`run_production.py`)

A unified script handles frontend asset verification and runs Uvicorn on all network interfaces (`0.0.0.0:8000`):

```bash
# 1. Install production dependencies
pip install -r requirements.txt

# 2. Run the production server
python run_production.py
```
FastAPI automatically serves `frontend/dist` with Single-Page Application (SPA) routing fallback for all paths, while preserving all `/api/...`, `/docs`, and `/ws/...` endpoints.

---

### Option C: Decoupled Cloud Deployment (Vercel + Render / Railway)

If hosting frontend and backend on separate platforms:

1. **Backend (Render / Railway / Fly.io / AWS ECS):**
   - Root directory: `EmergencyRoute-AI`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - Set Environment Variables in your platform's dashboard:
     ```
     TOMTOM_API_KEY=your_actual_key_here
     CORS_ORIGINS=https://your-frontend.vercel.app
     ```

2. **Frontend (Vercel / Netlify / Cloudflare Pages):**
   - Root directory: `EmergencyRoute-AI/frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Configure rewrite/proxy rule in `vercel.json` or `_redirects` to route `/api/*` to your backend URL.

---

## 3. Environment Variables Reference

| Variable | Required? | Default | Description |
| :--- | :--- | :--- | :--- |
| `TOMTOM_API_KEY` | Optional | `""` | Server-side key for live traffic flow, incident hazard alerts, and satellite layers. |
| `DELHIVERY_API_KEY` | Optional | `""` | Enterprise geocoding key (falls back to local OSM if absent). |
| `CORS_ORIGINS` | Optional | `"*"` | Comma-separated list of allowed origins (e.g. `https://my-domain.com`). |
| `API_HOST` | Optional | `"127.0.0.1"` | Bind address (`0.0.0.0` in Docker / production). |
| `API_PORT` | Optional | `8000` | Port number. |
| `LOG_LEVEL` | Optional | `"INFO"` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 4. Pre-Commit / Pre-Push Safety Checklist

Before committing or pushing code to any public GitHub or GitLab repository:

- [x] Run `git status` — confirm `.env` is **NOT** listed in untracked files.
- [x] Check `.env.example` — ensure all keys are empty strings (`""`).
- [x] Search repository for sensitive values — verify zero secrets are hardcoded in source code.
- [x] Run automated test suite: `pytest backend/tests -v` (68/68 passing).
- [x] Verify frontend build output in `frontend/dist` contains zero raw API keys.
