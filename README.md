# Salon Reservations API

System for managing event hall reservations with availability control.

## Features
- User authentication (JWT)
- Hall availability management
- Reservation lifecycle management

## Tech Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- Vanilla JS (frontend)

## Database Notes

### Reservation partial unique index (PostgreSQL vs SQLite)

The `reservations` model defines a partial unique index named `uq_hallid_resdate_active`.

- In PostgreSQL, this is enforced with `postgresql_where` and is already represented in the migration history.
- In SQLite (used by tests), the equivalent condition must be explicitly declared with `sqlite_where` on the SQLAlchemy `Index`.

Why this exists:

- PostgreSQL behavior is already covered by existing migrations.
- SQLite needs `sqlite_where` to mirror the same conditional uniqueness semantics during tests.
- Without `sqlite_where`, test behavior can diverge from production behavior for reservation slot uniqueness.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
