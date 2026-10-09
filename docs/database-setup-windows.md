# Database setup on Windows (PostgreSQL, no Docker)

About 20 minutes. You do this once.

The API works without a database (mock mode), so nothing here blocks the designers. The database turns on real login now and will hold campaigns, contacts and responses as each endpoint moves over.

## 1. Install PostgreSQL

1. Download the Windows installer from **postgresql.org/download/windows** (version 16 or 17 is fine).
2. Run it and keep the defaults, with these notes:
   - **Password for the `postgres` superuser:** choose one and write it down. You need it in step 3.
   - **Port:** leave 5432.
   - **Components:** keep PostgreSQL Server, pgAdmin 4 and Command Line Tools. You can untick Stack Builder.
3. Finish the install. PostgreSQL now runs in the background as a Windows service and starts with your computer.

## 2. Open a SQL prompt as the superuser

Easiest: open **SQL Shell (psql)** from the Start menu, press Enter through the first four questions (server, database, port, username), then type the `postgres` password from step 1.

Or in PowerShell (change `17` to your version):
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
```

## 3. Create the app user and the databases

Paste these lines one at a time. Choose your own password, and use only letters and numbers, so it needs no special handling in a URL.

```sql
CREATE USER eventreach WITH PASSWORD 'choose-a-password';
CREATE DATABASE eventreach OWNER eventreach ENCODING 'UTF8' TEMPLATE template0;
CREATE DATABASE eventreach_test OWNER eventreach ENCODING 'UTF8' TEMPLATE template0;
\q
```

`ENCODING 'UTF8'` is not optional. Without it, Hindi, Malayalam and Tamil names cannot be saved, and the setup script will refuse to continue.

## 4. Tell the API where the database is

Copy `.env.example` to a new file named `.env` in the repo root (never commit it), and set these lines, using your password:

```
DATABASE_URL=postgresql://eventreach:choose-a-password@localhost:5432/eventreach
TEST_DATABASE_URL=postgresql://eventreach:choose-a-password@localhost:5432/eventreach_test
SECRET_KEY=<paste a long random string>
```

To make a `SECRET_KEY`, run this and paste the output:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 5. Install the new packages and create the tables

In the `api` folder, with your venv active:

```powershell
pip install -r requirements-dev.txt
python scripts/init_db.py
```

You should see: `Tables created. The 4 template presets are loaded.` You can run it again safely.

## 6. Create your own account

```powershell
python scripts/create_organizer.py --email you@example.com --name "Your Name" --admin
```
It asks for a password on screen. Use at least 8 characters.

## 7. Check that it works

1. Restart the server: `uvicorn app.main:app --reload --port 8000`.
2. Open `http://localhost:8000/health`. You should see `"database": "connected"`.
3. Open `http://localhost:8000/docs`, run `POST /auth/login` with your email and password, and copy the `access_token` from the response.
4. Click the **Authorize** button at the top right, paste the token, and click Authorize.
5. Run `GET /me`. It should show your name and `"role": "admin"`.
6. Run the tests: `pytest`. With `TEST_DATABASE_URL` set, the database tests run too (about 20 more tests).

## What works with the database today

| Part | Status |
|---|---|
| Organizer sign-up, login, `/me` | Real, stored in PostgreSQL |
| Template presets | Loaded into the database (the API still serves them from code) |
| Campaigns, contacts, translations, analytics, registration, payments | Still mock. They move to the database one endpoint at a time |

If `DATABASE_URL` is empty, everything runs in mock mode and any login works. That is what the designers use.

## Troubleshooting

| What you see | What it means and the fix |
|---|---|
| `connection refused` or "Is the server running" | PostgreSQL is not running. Press the Windows key, type **Services**, find `postgresql-x64-17`, and click Start |
| `password authentication failed` | The password in `DATABASE_URL` is wrong. Reset it in psql: `ALTER USER eventreach WITH PASSWORD 'new-password';` |
| `database "eventreach" does not exist` | Step 3 did not finish. Run it again |
| `uses WIN1252 encoding` (or another non-UTF8 name) | The database was created without `ENCODING 'UTF8'`. In psql as `postgres`: `DROP DATABASE eventreach;` then create it again with the line from step 3 |
| `psql is not recognized` | Windows did not add it to PATH. Use the SQL Shell from the Start menu, or the full path shown in step 2 |
| The password has `@` or `#` in it | Special characters must be URL-encoded in `DATABASE_URL`. Simplest: choose a password of letters and numbers |
| Everyone is signed out after a restart | `SECRET_KEY` is missing or shorter than 32 characters, so the API used a temporary key. Set it in `.env` |

## Safety notes

- Keep `.env` out of git. It is already in `.gitignore`.
- Use made-up people only until the privacy controls (encryption of phone numbers, retention) are in place.
- `python scripts/init_db.py --reset` deletes everything in the database. It only runs on a database on your own computer, and asks you to confirm.
- Sign-up is open by default so you can try it. To close it, set `ALLOW_REGISTRATION=false` in `.env` and create accounts with the script.

## For code that reads the database later

- Always `conn.commit()` after a write. The helper in `app/db.py` does not do it for you.
- Phone numbers will be stored encrypted (`phone_enc`) and hashed (`phone_hash`). Never log a full number.
- psycopg returns arrays of custom enum types (like `channel[]`) as text. Add `::text[]` to the column in your query to get a Python list.
