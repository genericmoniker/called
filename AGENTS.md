# Called — AI Agent Instructions

Called is a Django kiosk app that displays a rotating slideshow of missionaries
on a TV screen connected to a Raspberry Pi. The board auto-rotates every 30
seconds via HTML `meta refresh`.

## Dev commands

```bash
# Activate venv first
source .venv/bin/activate

python manage.py runserver          # dev server (uses instance/db.sqlite3)
python manage.py migrate            # apply migrations
python manage.py makemigrations     # create migrations after model changes
python manage.py collectstatic      # collect static → instance/staticfiles/
python manage.py createsuperuser    # create admin user

ruff check --fix .                  # lint + autofix
ruff format .                       # format
```

Tests are not yet implemented (`apps/*/tests.py` are empty stubs).

## Architecture

```
apps/board/         ← board display, SW, photo transform AJAX
apps/missionaries/  ← Missionary + Ward models, rich admin UI
apps/filters/       ← add_class template tag for DaisyUI form fields
called/             ← Django project settings/urls
instance/           ← gitignored: db.sqlite3, media/, staticfiles/
deployment/         ← DigitalOcean + Raspberry Pi deployment scripts
```

**Request flow**: Nginx → Gunicorn → Django → WhiteNoise (static files)

The board shows 6 missionaries per page, ordered by last name, filtered to those
within 30 days of their `end_date`.

## Frontend

- **Tailwind CSS 4 + DaisyUI 5** loaded from CDN (no npm/node build step)
- Vanilla JS only — no frontend framework
- The board CSS targets 4K displays (3840×2160px); a JS viewport transform
  scales it to any screen
- `apps/board/service-worker.js` uses network-first caching. **Bump `CACHE_NAME`
  (e.g. `board-v14`) whenever changing cached resources** (HTML, static files,
  media)
- See [docs/offline-support.md](docs/offline-support.md) for SW architecture
  details

## Key conventions

- **Python 3.13+, Django 5.2+**
- **Ruff** lints with `select = ["ALL"]` — fix violations before committing; see
  ignored rules in `pyproject.toml`
- Pre-commit runs `ruff-check --fix` and `ruff-format` automatically
- Migrations live in `apps/*/migrations/` — never edit manually; always use
  `makemigrations`
- Skip migrations directory in Ruff: already excluded in `pyproject.toml`
- `instance/` holds runtime data (DB, uploads, collected static) and is
  gitignored — never commit it
- Photo transform values (`photo_scale`, `photo_translate_x/y`) are edited live
  via the admin preview at `/board/preview/`

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Required in production |
| `DJANGO_DEBUG` | `True` | Set `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated |
| `SENTRY_DSN` | (none) | Optional error tracking |

## Deployment

Server: DigitalOcean droplet via `deployment/server/do-deploy.py` (requires
`deployment/server/.env`). See [README.md](README.md#deployment) for full setup.

Client: Raspberry Pi systemd service opens a browser to the board URL. See
`deployment/client/`.
