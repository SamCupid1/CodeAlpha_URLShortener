# CodeAlpha URL Shortener

Linkwell is a Django URL-shortening service with account registration, click analytics, QR codes, and an owner-scoped JSON API. The project uses PostgreSQL when `DATABASE_URL` is configured and SQLite by default for a quick local start.

## Features

- Create short links as a guest or from an authenticated workspace.
- Register with a username, email address, and password; accounts are active immediately, then sign in to access the dashboard.
- Sign in with a username or email address (case-insensitive); passwords remain case-sensitive.
- View owned links, click totals, a 14-day click chart, and QR codes on the dashboard.
- Copy short links, remove owned links, and redirect with click-event tracking.
- Browse and create owned links through the authenticated JSON API.
- Manage links and inspect click events in Django Admin.
- Protect forms and session-authenticated API writes with Django CSRF middleware.
- Limit anonymous link creation to 10 requests per hour per IP address.
- Serve collected static files with WhiteNoise.

## Tech stack

- Python 3.12+ and Django 5.2 or 6.0
- PostgreSQL in deployment; SQLite for local development
- Tailwind CSS and DaisyUI, loaded from their public CDNs
- Chart.js for dashboard analytics
- `django-ratelimit`, Redis-compatible cache support, QR generation, and WhiteNoise

## Local setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks environment activation, run the commands with `.venv\Scripts\python.exe` instead.

Open `.env` and replace `SECRET_KEY` with a private random value.

### 2. Use PostgreSQL (optional for local development)

Without `DATABASE_URL`, Django creates `db.sqlite3` in the project directory. To use PostgreSQL, create a database and configure `.env`:

```text
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/url_shortener
```

The PostgreSQL server and database must exist before running migrations. `psycopg` is installed from `requirements.txt`.

### 3. Create database tables and an administrator

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the application

```powershell
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The dashboard is at `/dashboard/`, and Django Admin is at `/admin/`.

## API

API access uses Django session authentication. Sign in in a browser first; POST and DELETE requests must include a valid CSRF token (send it in the `X-CSRFToken` header for JavaScript clients).

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/urls/` | List the signed-in user's links (50 per page; optional `?page=2`). |
| `POST` | `/api/urls/` | Create a link with a JSON body such as `{"url":"https://example.com/article"}`. |
| `GET` | `/api/urls/<short_code>/` | Retrieve one of the signed-in user's links. |
| `DELETE` | `/api/urls/<short_code>/` | Delete one of the signed-in user's links. |

Create responses include the original `url`, `short_code`, absolute `short_url`, click count, and creation timestamp. Invalid URLs and malformed JSON return a `400` JSON response. Attempts to access another user's link return `404`.

Other useful routes:

| Route | Description |
| --- | --- |
| `/` | Public landing page and guest short-link form. |
| `/accounts/register/` | Registration form; new accounts can sign in immediately after registration. |
| `/accounts/login/` | Sign-in form. |
| `/dashboard/` | Signed-in user's dashboard and analytics. |
| `/<short_code>/` | Redirect to the original destination and record a click. |
| `/<short_code>/qr/` | PNG QR code for a short link. |
| `/admin/` | Django administration. |

## Deployment notes

- Set a unique `SECRET_KEY`, `DEBUG=False`, and the production hostname in `ALLOWED_HOSTS`.
- Set `DATABASE_URL` to a managed PostgreSQL database.
- Set `REDIS_URL` to a shared Redis instance so anonymous rate limits are consistent across workers. The default local-memory cache is intended only for development and single-process runs.
- Run `python manage.py migrate` and `python manage.py collectstatic --noinput` during deployment.
- On Linux, run the WSGI application with `gunicorn Codealpha.wsgi:application`.
- Serve the app behind HTTPS. Production settings enable HTTPS redirects and secure session/CSRF cookies.
- Enable `SECURE_HSTS_INCLUDE_SUBDOMAINS=True` and `SECURE_HSTS_PRELOAD=True` only if every subdomain is permanently HTTPS-only.
- Tailwind CSS, DaisyUI, Google Fonts, and Chart.js are loaded from public CDNs; the browser needs internet access to load those frontend assets.

## Screenshots

The landing page, account screens, and responsive dashboard are rendered by the templates in `URL_Shortener/templates/URL_Shortener/`. Add deployment screenshots here when captured.
