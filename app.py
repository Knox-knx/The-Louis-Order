from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps
from datetime import datetime
from github_sync import push_json

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

DATA_DIR = "data"

USERS_FILE = os.path.join(DATA_DIR, "users.json")
MEMBERS_FILE = os.path.join(DATA_DIR, "members.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.json")


def sync_all():

    push_json(
        MEMBERS_FILE,
        "data/members.json"
    )

    push_json(
        USERS_FILE,
        "data/users.json"
    )

    push_json(
        SETTINGS_FILE,
        "data/settings.json"
    )

    push_json(
        LOGS_FILE,
        "data/logs.json"
    )

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "owner":
            flash("Owner access required")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def add_log(action):

    logs = load_json(LOGS_FILE)

    if "logs" not in logs:
        logs["logs"] = []

    logs["logs"].append({
        "action": action,
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })

    save_json(LOGS_FILE, logs)

    sync_all()


@app.route("/logs")
@login_required
def logs():

    data = load_json(LOGS_FILE)

    return render_template(
        "logs.html",
        logs=reversed(data.get("logs", []))
    )


# =========================
# JSON HELPERS
# =========================

def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# =========================
# AUTH HELPERS
# =========================

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "owner":
            flash("Owner access required")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# =========================
# HOME
# =========================

@app.route("/")
def home():
    settings = load_json(SETTINGS_FILE)
    members = load_json(MEMBERS_FILE)

    return render_template(
        "home.html",
        settings=settings,
        members=members.get("members", [])
    )


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    settings = load_json(SETTINGS_FILE)

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_json(USERS_FILE)

        owner = users.get("owner", {})

        if (
            username == owner.get("username")
            and password == owner.get("password")
        ):
            session["user"] = username
            session["role"] = "owner"

            return redirect(url_for("dashboard"))

        for admin in users.get("admins", []):

            if (
                username == admin.get("username")
                and password == admin.get("password")
            ):
                session["user"] = username
                session["role"] = "admin"

                return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template(
        "login.html",
        settings=settings
    )

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
@login_required
def dashboard():

    users = load_json(USERS_FILE)
    members = load_json(MEMBERS_FILE)

    return render_template(
        "dashboard.html",
        total_members=len(members.get("members", [])),
        total_admins=len(users.get("admins", [])),
        role=session.get("role")
    )


# =========================
# MEMBERS
# =========================

@app.route("/members")
@login_required
def members():

    data = load_json(MEMBERS_FILE)

    return render_template(
        "members.html",
        members=data.get("members", [])
    )


# =========================
# ADD MEMBER
# =========================

@app.route("/member/add", methods=["GET", "POST"])
@login_required
def add_member():

    if request.method == "POST":

        data = load_json(MEMBERS_FILE)

        # Ensure members list exists
        if "members" not in data:
            data["members"] = []

        members = data["members"]

        new_member = {
            "id": max([m.get("id", 0) for m in members], default=0) + 1,
            "name": request.form.get("name", "").strip(),
            "telegram": request.form.get("telegram", "").strip(),
            "bio": request.form.get("bio", "").strip(),
            "roles": request.form.getlist("roles")
        }

        members.append(new_member)

        save_json(MEMBERS_FILE, data)

        sync_all()

        try:
            add_log(
                f"{session.get('user')} added member {new_member['name']}"
            )
        except:
            pass

        flash("Member added successfully")

        return redirect(url_for("members"))

    return render_template("member_add.html")


# =========================
# DELETE MEMBER
# =========================

@app.route("/member/delete/<int:member_id>")
@login_required
def delete_member(member_id):

    data = load_json(MEMBERS_FILE)

    data["members"] = [
        m for m in data.get("members", [])
        if m["id"] != member_id
    ]

    save_json(MEMBERS_FILE, data)

    sync_all()

    flash("Member removed")

    return redirect(url_for("members"))


# =========================
# ADMINS
# =========================

@app.route("/admins")
@login_required
@owner_required
def admins():

    users = load_json(USERS_FILE)

    return render_template(
        "admins.html",
        admins=users.get("admins", [])
    )


# =========================
# ADD ADMIN
# =========================

@app.route("/admin/add", methods=["POST"])
@login_required
@owner_required
def add_admin():

    users = load_json(USERS_FILE)

    if "admins" not in users:
        users["admins"] = []

    users["admins"].append({
        "username": request.form.get("username"),
        "password": request.form.get("password")
    })

    save_json(USERS_FILE, users)

    sync_all()

    flash("Admin added")

    return redirect(url_for("admins"))


# =========================
# SETTINGS
# =========================

@app.route("/settings", methods=["GET", "POST"])
@login_required
@owner_required
def settings():

    data = load_json(SETTINGS_FILE)

    if request.method == "POST":

        data["site_name"] = request.form.get("site_name")
        data["motto"] = request.form.get("motto")
        data["channel_link"] = request.form.get("channel_link")
        data["group_link"] = request.form.get("group_link")
        data["request_form"] = request.form.get("request_form")

        save_json(SETTINGS_FILE, data)

        sync_all()

        flash("Settings updated successfully")

    return render_template(
        "settings.html",
        settings=data
    )

# =========================
# Admin
# =========================

@app.route("/admin/delete/<int:index>")
@login_required
@owner_required
def delete_admin(index):

    users = load_json(USERS_FILE)

    admins = users.get("admins", [])

    if 0 <= index < len(admins):
        admins.pop(index)

    users["admins"] = admins

    save_json(USERS_FILE, users)

    sync_all()

    flash("Admin removed successfully")

    return redirect(url_for("admins"))


# =========================
# Members
# =========================


@app.route("/member/edit/<int:member_id>", methods=["GET", "POST"])
@login_required
def edit_member(member_id):

    data = load_json(MEMBERS_FILE)

    member = next(
        (m for m in data.get("members", []) if m["id"] == member_id),
        None
    )

    if not member:
        flash("Member not found")
        return redirect(url_for("members"))

    if request.method == "POST":

        member["name"] = request.form.get("name")
        member["telegram"] = request.form.get("telegram")
        member["bio"] = request.form.get("bio")
        member["roles"] = request.form.getlist("roles")

        save_json(MEMBERS_FILE, data)

        sync_all()

        flash("Member updated")

        return redirect(url_for("members"))

    return render_template(
        "member_edit.html",
        member=member
    )



@app.route("/category/<role>")
def category(role):

    data = load_json(MEMBERS_FILE)

    members = []

    for member in data.get("members", []):

        if role in member.get("roles", []):
            members.append(member)

    return render_template(
        "category.html",
        role=role,
        members=members
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)