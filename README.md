# ECharts Lab Private (MVP)

A private, self-hosted web app that mimics the **ECharts online editor** experience:
- Monaco editor (JSON option)
- Live ECharts preview
- Login + role-based access (admin/editor/viewer)
- Project save/load with version history (PostgreSQL)
- Export chart as PNG and export option JSON

## Quick Start (Docker Compose)

Prerequisite:
- Docker Desktop (Windows/macOS) or Docker Engine (Linux)

1. Install Docker + Docker Compose.
2. From the project root:

```bash
docker compose up --build
```

3. Open:
- Web: http://localhost:8080

Health check:
- http://localhost:8080/api/health

## Default Accounts

On first startup, the backend seeds an admin user (if it doesn't already exist):
- Username: `admin`
- Password: `admin123`

You can change these in `.env` before first run.

## RBAC (admin/editor/viewer)

- `viewer`: read-only (cannot create projects / save versions)
- `editor`: can create projects and save versions
- `admin`: editor permissions + can create users

Create users (admin only):

```bash
curl -X POST http://localhost:8080/api/auth/users \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"pass123","role":"editor"}'
```

## What You Get (MVP)

- **Login**
- **Projects list**
  - Create project
  - Load project
- **Editor**
  - Edit ECharts `option` as JSON
  - JSON validation errors panel
- **Preview**
  - Live render
  - Export PNG
- **Save**
  - Save creates a new version; you can view versions list (basic)

## Folder Structure

- `backend/` FastAPI + SQLAlchemy + PostgreSQL
- `frontend/` Vue 3 + Vite + TypeScript + ECharts + Monaco
- `web/` Nginx container that serves the built frontend and proxies `/api` to backend
- `docker-compose.yml` One-command deployment

## Local Dev (optional)

### Backend
```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend dev server proxies `/api` to `http://localhost:8000`.

## Notes on "Uploading/Editing Code"

This MVP supports **JSON-only** ECharts option (safe path). If you later want to support `option.js` with functions
(formatter, custom logic), you must run user code in a sandbox (e.g., sandboxed iframe/worker) to avoid XSS.

## If you don't have Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg2://echarts:echarts_pw@localhost:5432/echarts_lab"
$env:JWT_SECRET="change_me_in_production"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="admin123"
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open:
- http://localhost:5173
