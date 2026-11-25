# Northvale University – Information & Announcements Portal

Cloud Computing project: design, deploy and compare a dynamic web application.

**Team:** Salem Bakhouche · Fechit Mohammed Idris · Djwaher Yacine · Saadi Mohammed

Flask (Python 3.12) + PostgreSQL 16, deployed in two environments:

| | Environment 1 – IaaS-style | Environment 2 – PaaS |
|---|---|---|
| Host | VirtualBox → Ubuntu Server 24.04 VM → Docker | Render |
| App | `uni-web` container (gunicorn) | Render Web Service (same Dockerfile) |
| DB | `uni-db` container (postgres:16-alpine) | Render PostgreSQL |
| Persistence | named volume `uni_pgdata` | managed DB storage |
| Config | `.env` file → compose env vars | Render env vars (`render.yaml`) |

## Features
- Home page: university presentation + 3 most recent announcements
- Departments page (from the DB)
- News & announcements page (from the DB)
- Admin (login required): create, edit, delete announcements
- `/health` endpoint that checks DB connectivity

## Project layout
```
app/
  app.py            Flask routes, DB access, login
  schema.sql        tables + fictional sample data (idempotent, run at start-up)
  templates/        Jinja2 HTML pages
  static/style.css
Dockerfile          image used in the VM and on Render
docker-compose.yml  web + db containers, networks, volume (Environment 1)
render.yaml         Render Blueprint (Environment 2)
.env.example        configuration template
```

## Environment 1 – Docker in the Ubuntu VM
```bash
git clone https://github.com/SalemBeck/university-portal.git
cd university-portal
cp .env.example .env        # then edit the passwords
docker compose up -d --build
docker compose ps
```
Open `http://<VM-host-only-IP>:8080` from the physical host (e.g. `http://192.168.56.10:8080`).

Persistence test:
```bash
docker exec -it uni-db psql -U university -d university -c "SELECT id,title FROM announcements;"
docker compose rm -sf db          # remove the PostgreSQL container
docker compose up -d db           # recreate it with the same volume uni_pgdata
docker exec -it uni-db psql -U university -d university -c "SELECT id,title FROM announcements;"
```

## Environment 2 – Render
1. Render dashboard → **New → Blueprint** → select this repository.
2. Render reads `render.yaml`, creates `university-db` (PostgreSQL) and `university-portal` (web service).
3. Enter `ADMIN_PASSWORD` when asked. `DATABASE_URL` is injected from the database automatically.
