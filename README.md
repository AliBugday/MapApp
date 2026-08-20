# MapApp

MapApp is a location-based civic and community platform. People can drop a pin on a map to report
an issue, request something for their neighborhood, or find local
events and announcements — then upvote, comment on, and share what's already there. Municipalities
and organizations can post as verified accounts. This repo is a demo/MVP: Django/DRF + PostGIS
backend, Next.js/TypeScript frontend.

## Prerequisites

- Docker
- Docker Compose (v2, the `docker compose` CLI)

## Setup

1. Copy the environment file and adjust if needed:

   ```
   cp .env.example .env
   ```

2. Start the stack:

   ```
   docker compose up
   ```

3. Run database migrations:

   ```
   docker compose exec backend python manage.py migrate
   ```

4. (Optional) Seed demo data — creates ~28 sample reports around Ankara,
   with demo users and organizations:

   ```
   docker compose exec backend python manage.py seed_demo_data --flush
   ```

   `--flush` is required on every run after the first — it resets demo users/reports before
   reseeding.

5. (Optional) Create a superuser for Django admin access:

   ```
   docker compose exec backend python manage.py createsuperuser
   ```

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django admin: http://localhost:8000/admin

## Demo accounts

If you ran the seed command, every seeded user (citizens and organizations) shares the password
`demo12345678`. For example:

- Citizen: `mehmet.ozturk`
- Organization: `ankara.buyuksehir.belediyesi`

## Tests

Backend:

```
docker compose exec backend pytest -q
docker compose exec backend ruff check .
```

Frontend:

```
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
```
