# User Management API (FastAPI)

JWT auth (access + refresh), RBAC (admin/user), SQLAlchemy ORM, CRUD, limit/offset pagination,
CORS, logging and middleware.

## Project structure
```
user_management_api/
├── app/
│   ├── main.py                    # app factory: middleware, CORS, routers, lifespan
│   ├── core/
│   │   ├── config.py              # settings (env / .env)
│   │   ├── security.py            # bcrypt hashing + JWT create/decode
│   │   ├── logging.py             # console + rotating file logging
│   │   └── exceptions.py          # global error handlers
│   ├── db/
│   │   ├── base.py                # declarative Base
│   │   ├── session.py             # engine, SessionLocal, get_db dependency
│   │   └── init_db.py             # create tables + seed admin
│   ├── models/user.py             # SQLAlchemy User + Role enum
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── user.py
│   │   └── auth.py
│   ├── crud/user.py               # all DB queries (no HTTP concerns)
│   ├── api/
│   │   ├── deps.py                # get_current_user, require_admin
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/{auth,users}.py
│   └── middleware/request_logging.py
├── tests/test_api.py
├── logs/
├── .env.example
├── requirements.txt
└── README.md
```

## Setup & run
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # optional (Windows: copy .env.example .env)
uvicorn app.main:app --reload
```
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Seeded admin: `admin@example.com` / `Admin@12345`

## Run tests
```bash
pytest -q
```

## Endpoints (prefix /api/v1)
| Method | Path | Access |
|---|---|---|
| POST | /auth/register | public (role always `user`) |
| POST | /auth/login | public (form: username=email, password) |
| POST | /auth/refresh | public (valid refresh token) |
| GET | /users/me | any authenticated user |
| GET | /users?limit=&offset=&search= | admin |
| POST | /users | admin |
| GET | /users/{id} | admin, or the user themself |
| PATCH | /users/{id} | admin, or the user themself (not role/is_active) |
| DELETE | /users/{id} | admin (not self) |

## Demo checklist (Swagger)
1. Register -> 201; duplicate -> 409; short password -> 422
2. Login -> access + refresh tokens; wrong password -> 401
3. Authorize (top right) -> GET /users/me -> 200
4. POST /auth/refresh with refresh token -> new pair; access token in refresh -> 401
5. As user: GET /users -> 403; PATCH own role -> 403. As admin: both work
6. CRUD as admin; missing id -> 404; delete self -> 400
7. GET /users?limit=3&offset=0, then offset=3; limit=0 -> 422
8. Check response headers `x-request-id`, `x-process-time-ms` and `logs/app.log`

Short-lived token demo: `ACCESS_TOKEN_EXPIRE_MINUTES=1 uvicorn app.main:app --reload`
