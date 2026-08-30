# Clinic CS

A chatbot and booking system for aesthetic clinics in Indonesia.

Customers chat in Bahasa Indonesia to ask about treatments and book an appointment. Clinic staff log into a dashboard to see those bookings and confirm or cancel them.

The bot answers questions using RAG over a clinic knowledge base, and handles booking by asking for one thing at a time (treatment, branch, date, time, name). Chat sessions are kept in Redis.

## What it does

For customers:
- Answers FAQ using the clinic knowledge base
- Takes a booking through chat
- Shows quick reply buttons based on what the bot just said
- Remembers the current conversation (stored in Redis)

For clinic staff:
- Login with email and password
- Stays logged in after a page refresh
- Booking list with a status filter and Confirm / Cancel / Complete buttons
- Stats page (today, this week, pending, confirmed), refreshes every 30s
- Only ADMIN users can open the dashboard

## Built with

Backend:
- FastAPI
- PostgreSQL with SQLAlchemy 2.0 (async) and Alembic
- Redis for chat sessions, refresh tokens, and the stats cache
- LangChain and Chroma for RAG
- Ollama running qwen2.5:14b
- bcrypt and PyJWT for login

Frontend:
- React 19, TypeScript, Vite
- Tailwind CSS, shadcn/ui
- react-router-dom
- Zustand for auth state

Postgres and Redis run in Docker. The backend runs on the host.

## Folders

```
api/routes/       endpoints: chat, auth, bookings, health
auth/             JWT, password hashing, refresh tokens
booking/          intent, slot extraction, validation, session and stats storage
db/               database connection
models/           tables and request/response schemas
migrations/       Alembic
scripts/          seed_admin.py and manual tests
chatbot.py        main conversation logic
rag.py, vector.py RAG setup
main.py           app entry point

frontend/src/
  features/chat/  chat widget
  features/admin/ dashboard pages
  features/auth/  auth store, session restore, route guard
  lib/            fetch wrapper (adds the token, retries after refresh)
```

## Running it

**1. Database and Redis**

```bash
docker compose up -d
```

**2. Backend**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill this in
python -m alembic upgrade head
python -m scripts.seed_admin
uvicorn main:app --reload
```

Runs on http://localhost:8000. Docs at /docs.

Ollama has to be running too:

```bash
ollama pull qwen2.5:14b
```

**3. Frontend**

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Runs on http://localhost:5173. Chat is at `/`, dashboard is at `/admin`.

## Endpoints

| Method | Path | Who can call it |
|--------|------|-----------------|
| POST | `/api/chat` | anyone |
| POST | `/api/auth/login` | anyone |
| POST | `/api/auth/refresh` | needs the cookie |
| POST | `/api/auth/logout` | needs the cookie |
| GET | `/api/auth/me` | logged in |
| GET | `/api/admin/bookings` | admin |
| GET | `/api/admin/bookings/{id}` | admin |
| PATCH | `/api/admin/bookings/{id}/status` | admin |
| DELETE | `/api/admin/bookings/{id}` | admin |
| GET | `/api/admin/stats` | admin |
| GET | `/api/health` | anyone |

## Notes

- The access token lasts 15 minutes and is only kept in memory. The refresh token lasts 7 days and lives in an httpOnly cookie, so a page refresh does not log you out.
- Restarting the Redis container wipes chat sessions and refresh tokens, so everyone gets logged out.
- The stats endpoint saves its result in Redis for 30 seconds so it does not run the same 4 queries over and over. Any booking change deletes that saved value right away, so the numbers on screen are never stale because of it.

## Where it's going

Still being built. Next up is making the bot handle real Indonesian input better, maybe getting it onto WhatsApp, then try to find clinic to actually use it.
