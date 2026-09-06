# ⚜️ THE LOUIS ORDER ⚜️

> Learn • Build • Earn • Grow Together

**The Louis Order** is a Flask-based community / organization management website. It provides a public homepage showcasing the organization's vision and divisions, plus a private Owner/Admin panel to manage members, admins, site settings, and activity logs.

All data is stored in simple JSON files (`data/` folder) and optionally auto-synced back to GitHub so data survives restarts on free cloud hosting (Render / Railway / Heroku-style ephemeral disks).

---

## Table of Contents

- [What Is This?](#what-is-this)
- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Roles & Permissions](#roles--permissions)
- [Routes](#routes)
- [Data Model](#data-model)
- [GitHub Auto-Sync](#github-auto-sync)
- [Getting Started (Local Setup)](#getting-started-local-setup)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [Usage Guide](#usage-guide)
- [Security Notes](#security-notes)
- [Limitations & Future Improvements](#limitations--future-improvements)

---

## What Is This?

A small membership-management web app for a tech community called **THE LOUIS ORDER**.

Public visitors see:

- Hero section + Vision statement
- 11 Organization Divisions (Developer, Programmer, Security Researcher, Bot Developer, Web Developer, App Developer, UI/UX Designer, Digital Marketer, Seller, Innovator, Encoder/Decoder)
- Category pages (`/category/<role>`) listing members in each division

Logged-in users (Owner / Admins) get:

- Dashboard with stats (total members, total admins, categories, own role)
- Add / Edit / Delete organization members (name, Telegram, bio, roles)
- Owner-only: Add / Remove admins, edit site settings (site name, motto, Telegram links, request form)
- Activity log page (`/logs`) tracking who added whom

Think of it as a **mini-CMS + member directory**, built without a database — just Flask + Jinja templates + JSON files.

---

## Features

| Area | Details |
|---|---|
| 🌍 Public site | Homepage with vision + division grid, per-division category pages |
| 👥 Member management | Add, edit, delete, list. Each member has `id`, `name`, `telegram`, `bio`, `roles[]` |
| 🔐 Auth | Session-based login with 2 roles: `owner` (single, from `users.json`) and `admin` (multiple) |
| ⚜️ Admin management | Owner can add/remove admins (username + password) |
| ⚙️ Settings | Owner can edit `site_name`, `motto`, `channel_link`, `group_link`, `request_form` |
| 📝 Activity logs | Every member-add is logged with username + timestamp, viewable at `/logs` |
| ☁️ GitHub sync | Every write calls `sync_all()` → pushes all 4 JSON files to GitHub via PyGithub |
| 📱 Responsive UI | Shared `base.html` layout with top navbar + mobile bottom nav, custom CSS |
| 🚀 Deploy-ready | `Procfile` (`web: gunicorn app:app`) + `requirements.txt` for Render/Heroku/Railway |

---

## How It Works

### 1. Request flow

```
Browser → Flask (app.py) → load_json(data/*.json)
        → render_template(templates/*.html)
        → POST forms → save_json() → sync_all() → GitHub push → redirect + flash message
```

### 2. Authentication

- `GET /login` renders login form. `POST /login` checks credentials against `data/users.json`:
  - Match `users.owner` → `session = {user, role: "owner"}`
  - Else loop `users.admins[]` → `session = {user, role: "admin"}`
  - Else `flash("Invalid credentials")`
- `login_required` decorator redirects to `/login` if `"user"` not in session.
- `owner_required` decorator redirects to `/dashboard` with flash if `session.role != "owner"`.
- `GET /logout` clears session.

### 3. Members

- Stored in `data/members.json` as `{ "members": [ {id, name, telegram, bio, roles[]} ] }`.
- `GET /members` — list all (login required).
- `GET+POST /member/add` — form (`member_add.html` + `static/js/member_roles.js` for role checkboxes). New `id = max(existing ids) + 1`. Saves, syncs, logs `"<user> added member <name>"`.
- `GET+POST /member/edit/<id>` — pre-fills `member_edit.html` / `members_edit.html`, updates fields + `roles = request.form.getlist("roles")`. Saves, syncs.
- `GET /member/delete/<id>` — filters out member by id. Saves, syncs.
- `GET /category/<role>` — **public**, filters members where `role in member.roles`. Renders `category.html`.

### 4. Admins (owner-only)

- `GET /admins` — list `users.admins[]`.
- `POST /admin/add` — appends `{username, password}`.
- `GET /admin/delete/<index>` — removes admin by list index.

### 5. Settings (owner-only)

- `GET+POST /settings` — edits `data/settings.json` fields: `site_name`, `motto`, `channel_link`, `group_link`, `request_form`. The login page's "Request Admin Access" button links to `request_form` (a Google Form URL by default).

### 6. Logs

- `add_log(action)` appends `{action, time: "%Y-%m-%d %H:%M:%S"}` to `data/logs.json`, then saves + syncs.
- `GET /logs` (login required) renders them newest-first via `reversed(...)`.

### 7. Persistence

- Helpers `load_json()` / `save_json()` read/write JSON with `indent=4`. `load_json` returns `{}` on any error (missing/corrupt file).
- After **every** mutation (`add/edit/delete member`, `add/delete admin`, `settings change`, `log write`), `sync_all()` pushes all 4 JSON files to GitHub — this is what keeps data alive on hosts with ephemeral filesystems.

---

## Tech Stack

- **Backend:** Python + Flask (sessions, flash, Jinja2 templates)
- **Frontend:** HTML (Jinja), CSS (`static/css/style.css`), vanilla JS (`static/js/member_roles.js`), Google Fonts (Cinzel + Poppins)
- **Storage:** Flat JSON files in `data/` — no database
- **Sync:** PyGithub (`github_sync.py`)
- **Server:** gunicorn (production via `Procfile`), Flask dev server locally
- **Hosting target:** Render / Railway / Heroku (any host supporting `Procfile`)

---

## Project Structure

```
the-louis-order/
├── app.py                 # Entire Flask app: routes, auth, JSON helpers, logging
├── github_sync.py         # push_json() — pushes a local JSON file to GitHub via API
├── requirements.txt       # Flask, gunicorn, PyGithub
├── Procfile               # web: gunicorn app:app
├── data/
│   ├── users.json         # { owner: {username, password}, admins: [...] }
│   ├── members.json       # { members: [ {id, name, telegram, bio, roles[]} ] }
│   ├── settings.json      # { site_name, motto, channel_link, group_link, request_form }
│   └── logs.json          # { logs: [ {action, time} ] }
├── templates/
│   ├── base.html          # Navbar, flash messages, footer, mobile bottom-nav
│   ├── home.html          # Hero + Vision + 11 division cards
│   ├── login.html         # Owner/Admin login + "Request Admin Access" link
│   ├── dashboard.html     # Stats + action cards + category overview
│   ├── members.html       # Member cards grid with Edit/Delete
│   ├── member_add.html    # Add-member form
│   ├── members_edit.html / member_edit.html  # Edit-member form (see note below)
│   ├── category.html      # Public per-role member list
│   ├── categories.html    # (extra/legacy categories view)
│   ├── admins.html        # Owner: list/add/remove admins
│   ├── settings.html      # Owner: site settings form
│   └── logs.html          # Activity log list
└── static/
    ├── css/style.css
    ├── js/member_roles.js # Role-checkbox helper for add/edit forms
    └── images/
```

> ⚠️ Template note: `app.py` renders `member_edit.html` (singular) but the repo also contains `members_edit.html` (plural). Make sure the filename matches what `edit_member()` renders, or rename one to avoid `TemplateNotFound`.

---

## Roles & Permissions

| Action | Public | Admin | Owner |
|---|---|---|---|
| View home, category pages | ✅ | ✅ | ✅ |
| Login / logout | ✅ | ✅ | ✅ |
| Dashboard, members list, logs | ❌ | ✅ | ✅ |
| Add / edit / delete members | ❌ | ✅ | ✅ |
| Manage admins (`/admins`, `/admin/add`, `/admin/delete`) | ❌ | ❌ | ✅ |
| Edit settings (`/settings`) | ❌ | ❌ | ✅ |

Default owner (change immediately — see Security Notes):

```json
{ "owner": { "username": "louis", "password": "kvats2005@" }, "admins": [] }
```

---

## Routes

| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/` | public | Homepage (settings + members) |
| GET/POST | `/login` | public | Login form / authenticate |
| GET | `/logout` | — | Clear session → home |
| GET | `/dashboard` | login | Stats: members, admins, categories, role |
| GET | `/members` | login | All members grid |
| GET/POST | `/member/add` | login | Add member form + create |
| GET/POST | `/member/edit/<id>` | login | Edit member form + update |
| GET | `/member/delete/<id>` | login | Delete member |
| GET | `/category/<role>` | public | Members filtered by role |
| GET | `/admins` | owner | List admins |
| POST | `/admin/add` | owner | Add admin |
| GET | `/admin/delete/<index>` | owner | Remove admin by index |
| GET/POST | `/settings` | owner | View/update site settings |
| GET | `/logs` | login | Activity log (newest first) |

---

## Data Model

**`members.json`**
```json
{
  "members": [
    {
      "id": 1,
      "name": "Louis",
      "telegram": "@LouisPY",
      "bio": "",
      "roles": ["Developer", "Bot Developer", "Web Developer"]
    }
  ]
}
```

**`users.json`**
```json
{
  "owner": { "username": "louis", "password": "kvats2005@" },
  "admins": [{ "username": "admin1", "password": "secret" }]
}
```

**`settings.json`**
```json
{
  "site_name": "⚜️ 𝑻𝒉𝒆 𝑳𝒐𝒖𝒊𝒔 𝑶𝒓𝒅𝒆𝒓 ⚜️",
  "motto": "Learn • Build • Earn • Grow Together",
  "channel_link": "",
  "group_link": "",
  "request_form": "https://docs.google.com/forms/..."
}
```

**`logs.json`**
```json
{
  "logs": [{ "action": "louis added member Louis", "time": "2026-06-20 11:43:46" }]
}
```

---

## GitHub Auto-Sync

`github_sync.py`:

```python
push_json(local_file, github_file)  # reads local file, update-or-create on GitHub
```

`app.py → sync_all()` pushes all four files on every write:

- `data/members.json`, `data/users.json`, `data/settings.json`, `data/logs.json`

Activated only when **both** env vars are set; otherwise it prints `GitHub sync disabled` and skips (safe for local dev). Each call makes up to 4 GitHub API commits — fine for low traffic, but be aware of API rate limits if writes become frequent.

---

## Getting Started (Local Setup)

**Requirements:** Python 3.8+

```bash
# 1. Clone / enter project
cd the-louis-order

# 2. Create + activate virtualenv
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) enable GitHub sync — otherwise data stays local only
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_REPO="username/repo-name"   # e.g. "louis/the-louis-order"

# 5. Run
python app.py
# or
flask --app app run --debug

# 6. Open
# Public site: http://127.0.0.1:5000/
# Login:       http://127.0.0.1:5000/login
```

> Flask secret key is hardcoded as `"change_this_secret_key"` in `app.py` — set a proper random value before any real deployment.

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | Only for sync | Personal Access Token with `repo` (contents read/write) scope |
| `GITHUB_REPO` | Only for sync | Target repo as `owner/name`, e.g. `louis/the-louis-order` |
| `PORT` | On most hosts | Host injects it; gunicorn/Render handles automatically |
| `SECRET_KEY` | Recommended | Not yet wired — currently hardcoded in `app.py`; refactor to `os.getenv("SECRET_KEY", ...)` |

---

## Deployment

**Render (recommended for this layout):**

1. Push repo to GitHub.
2. Create → Web Service → connect repo.
3. Build: `pip install -r requirements.txt` · Start: `gunicorn app:app`.
4. Add env vars `GITHUB_TOKEN` + `GITHUB_REPO` (same repo or a separate data repo).
5. Deploy. Data writes will commit JSON back to GitHub automatically.

**Railway / Heroku:** same idea — Python app, `Procfile` start command `gunicorn app:app`, set the two `GITHUB_*` vars.

---

## Usage Guide

1. **Login** at `/login` with owner credentials (default `louis` / see `users.json`).
2. **Dashboard** shows counts. Click **Add Member** → fill name, Telegram (`@handle`), bio, tick one or more of the 11 roles → save.
3. **Members** page: edit or delete anyone. Deletion asks for JS confirm.
4. **(Owner) Admins** page: create admin logins (`username` + `password`), share them; remove via delete link. The login page's *Request Admin Access* Google Form is for applicants — owner reviews and creates the account manually.
5. **(Owner) Settings** page: update organization name, motto, Telegram channel/group links, request-form URL.
6. **Logs** page: audit who added whom and when.
7. **Public:** share `/` and `/category/<Division>` links (e.g. `/category/Bot Developer`) to showcase each division.

---

## Security Notes

- ⚠️ **Plaintext passwords** in `users.json` + default owner password committed to the repo. Change it immediately, hash passwords (e.g. `werkzeug.security`), and never commit real credentials.
- ⚠️ **Hardcoded `app.secret_key`.** Replace with `os.environ.get("SECRET_KEY")` and a long random value, or sessions can be forged.
- ⚠️ **Destructive GETs.** Delete routes (`/member/delete/<id>`, `/admin/delete/<index>`) use GET — crawlers/prefetchers could trigger them. Convert to POST + CSRF protection.
- ⚠️ **Duplicate `owner_required` definition** in `app.py` (defined twice). Harmless but clean it up.
- ⚠️ **No validation/sanitization.** Member/admin/settings inputs are stored raw. Add server-side validation and escape on render (Jinja auto-escapes by default — keep it that way).
- ⚠️ `GITHUB_TOKEN` with full `repo` scope is powerful — prefer a fine-grained token limited to the data repo, stored as a secret env var, never in code.

---

## Limitations & Future Improvements

- JSON-file storage: no concurrency control — simultaneous writes can clobber each other. Migrate to SQLite/PostgreSQL for real use.
- `load_json()` swallows all exceptions and returns `{}` — add logging to catch corrupt files.
- `add_log()` itself calls `sync_all()`, and callers like `add_member()` already called it → double GitHub pushes per action. Refactor to sync once.
- `edit_member` / `delete_member` / admin actions are not logged — extend `add_log` coverage.
- Delete-admin uses positional `index` — fragile; use stable IDs like members do.
- No search, pagination, avatars, password hashing, password change, or tests yet — good first contributions.

---

## License

No license file is included. Add one (e.g. MIT) if you want others to reuse this project.

---

*Built with Flask · Motto: Learn • Build • Earn • Grow Together* ⚜️
