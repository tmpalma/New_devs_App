# Database

## Local Postgres (Docker)

- **Schema + seed** run automatically when the `db` container is first created (see `docker-compose.yml` → `db` → `volumes`).
- Connect to DB **`propertyflow`** (e.g. `localhost:5433`, user `postgres`, password `postgres`).
- To re-run init (fresh schema + seed): `docker-compose down -v` then `docker-compose up -d`.

When **Supabase is not configured** (no `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`), the backend uses this local Postgres for **properties** and **reservations**, so Ocean and Sunset both see real data. Other features (auth, permissions, etc.) still use the in-app mock.
