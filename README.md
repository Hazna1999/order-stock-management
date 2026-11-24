# Order & Stock Management

![CI](https://github.com/YOUR_USERNAME/order-stock-management/actions/workflows/ci.yml/badge.svg)

Fullstack app (Django REST Framework + React/TypeScript). Staff maintain a product catalogue and customers, raise orders, move them through a lifecycle, and adjust stock. Stock is reserved atomically, so two users can never sell the same last units.

## Quick start (Docker)

```bash
docker compose up --build
```

Open http://localhost:5180 . Migrations and sample data are applied automatically. Swagger: http://localhost:8001/api/docs/

## Sample logins (password `Pass@1234`)

| User | Role |
|---|---|
| admin1 | Admin |
| sales1, sales2 | Sales User |
| inventory1 | Inventory Manager |

Accounts are created by an Admin (Users page or Django admin). There is no self-registration, by design.

## Local development

```bash
docker compose up -d db                      # PostgreSQL on localhost:5433
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate                     # also creates the three role groups
python manage.py seed_data                   # sample users, products, customers
python manage.py runserver 8001
```

```bash
cd frontend
npm install
npm run dev                                  # http://localhost:5180, proxies /api to 8001
```

Port 5433 avoids a clash with a local Postgres on 5432. If 8001 is busy, change it in `vite.config.ts`.

## Configuration

Copy `backend/.env.example` to `backend/.env`. Variables: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Docker Compose sets the database host and port itself. Frontend: `VITE_API_URL` (default `/api/v1`). Real `.env` files are git-ignored.

## Tests

```bash
cd backend && pytest -v        # 70 tests, needs PostgreSQL
cd frontend && npm test        # 8 tests
```

Backend: validation, price snapshot, server totals, idempotent confirm, stock restore, every invalid status transition (parametrised), edit lock, audit rows, permission matrix per role, and threaded concurrency tests on PostgreSQL. Frontend (Vitest + Testing Library): error parsing, role-based navigation, order action buttons.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request. Backend job: PostgreSQL service, `check`, migration drift check, pytest. Frontend job: lint, type check, tests, build.

## API

Base path `/api/v1/`, JWT in `Authorization: Bearer <token>`. Docs: Swagger at `/api/docs/`, OpenAPI file `backend/schema.yml` (regenerate with `python manage.py spectacular --file schema.yml`).

| Endpoint | Purpose |
|---|---|
| POST `/auth/login/`, `/auth/refresh/`; GET `/auth/me/` | JWT login, refresh, current user and roles |
| `/products/`, `/products/{id}/` | List (search, filter, ordering), create, retrieve, update |
| POST `/products/{id}/deactivate/`, `/products/{id}/adjust-stock/` | Soft delete, audited stock adjustment |
| GET `/products/categories/`, `/products/low-stock/` | Categories, products at or below reorder level |
| `/customers/`, `/customers/{id}/` | Customer CRUD |
| `/orders/`, `/orders/{id}/` | List (search, status/customer/product/date filters), nested create, edit DRAFT |
| POST `/orders/{id}/confirm/`, `ship/`, `deliver/`, `cancel/` | Lifecycle actions |
| GET `/orders/{id}/history/` | Audit trail |
| `/users/` | Admin-only user management |

Errors always look like `{"code": "...", "message": "...", "details": [...]}` with 400/401/403/404/409. Example: `insufficient_stock` lists every short product with requested and available quantities.

## Roles and permissions

Roles are Django groups, created by a data migration. Rules live in reusable permission classes (`common/permissions.py`); querysets restrict visibility.

| Capability | Admin | Sales User | Inventory Manager |
|---|---|---|---|
| View products | All | Active only | All |
| Create/edit/deactivate products | Yes | No | No |
| Adjust stock | Yes | No | Yes |
| Manage customers | Yes | Yes | No |
| View orders | All | Own | All |
| Create/edit DRAFT, confirm | Yes | Yes | No |
| Ship | Yes | No | Yes |
| Deliver | Yes | No | No |
| Cancel | Yes | Own orders | No |

401 for no/expired token, 403 for a missing role.

## Concurrency and locking

**Approach:** pessimistic row locking. `confirm`, `cancel`, `ship`, `deliver` and `adjust_stock` each run in `transaction.atomic` and use `select_for_update()`.

- The order row is locked first and its status is re-read after the lock, so two simultaneous confirms of one order cannot both deduct stock.
- Product rows are locked ordered by primary key, so orders with several products cannot deadlock.
- All short products are reported together.
- Repeating an action that already took effect returns 200 and changes nothing (no stock change, no audit row).
- Database constraints are a second line of defence: `stock_quantity >= 0`, case-insensitive unique SKU and email, one product per order.

**Why:** contention on the last units is the exact scenario in the requirements. The second request waits, then sees the real stock and fails with a clear error.

**Trade-offs:** requests touching the same rows are serialised, so throughput drops under heavy contention. A conditional atomic `UPDATE ... WHERE stock >= qty` holds locks more briefly but gives poorer error detail.

**Database:** SQLite ignores `select_for_update`, so the concurrency tests require PostgreSQL.

**Crash mid-confirmation:** the transaction never commits, so the database rolls back everything and stock and status stay consistent.

## Architecture and design decisions

- Layers: view (HTTP) -> serializer (validation) -> service (business rules, locks) -> model. Views stay thin.
- Order price is snapshotted per line; totals are computed on the server and read-only.
- Stock changes only through audited adjustments or order services; direct edits are rejected.
- Products and customers are never hard-deleted (`is_active`).
- URL versioning (`/api/v1/`) with a `urls.py` and router per app.
- Frontend: TanStack Query for server state (loading skeletons, optimistic status changes with rollback), React Context for auth, an axios interceptor that refreshes the JWT once on a 401, debounced search, error toasts that list stock shortages.
- Docker Compose runs db, backend (`runserver` for simplicity; gunicorn for production) and frontend (nginx).

## Not implemented / future work

- Idempotency-Key header on confirm (confirm is already naturally idempotent)
- Partial shipments (add Shipment/ShipmentItem and a shipped quantity per order line)
- Customer-specific pricing
- Browser end-to-end tests, wider frontend test coverage