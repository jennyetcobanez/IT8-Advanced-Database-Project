"""
Barangay Health Appointment and Management System
Flask backend. Talks to the MySQL database `barangay_health_system`.
Run:  python app.py   ->   http://127.0.0.1:5000
"""
import os
import hashlib
from datetime import date, datetime, timedelta
from functools import wraps

import pymysql
import pymysql.cursors
from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

DB_CONFIG = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "barangay_health_system"),
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)

APPT_STATUSES = ["Pending", "Approved", "Completed", "Cancelled", "Rejected"]
PROGRAM_STATUSES = ["Upcoming", "Ongoing", "Completed", "Cancelled"]
REG_STATUSES = ["Registered", "Attended", "Cancelled"]
SLOTS = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]


# ---------------------------------------------------------------- database helpers
def get_db():
    if "db" not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def q(sql, args=(), one=False):
    """Run a SELECT and return rows (or one row)."""
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        rows = cur.fetchall()
    if one:
        return rows[0] if rows else None
    return rows


def db_error(e):
    code = e.args[0] if e.args else 0
    msg = e.args[1] if len(e.args) > 1 else str(e)
    return f"The database rejected this action (error {code}): {msg}"


def run(sql, args=(), ok_msg=None):
    """Run INSERT/UPDATE/DELETE and commit. Returns affected rows, or None on error."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(sql, args)
            n = cur.rowcount
        db.commit()
        if ok_msg:
            flash(ok_msg, "ok")
        return n
    except pymysql.MySQLError as e:
        db.rollback()
        flash(db_error(e), "error")
        return None


def hash_pw(p):
    # Same method used by the seed data (SHA-256). Demo only: use bcrypt/argon2 in real systems.
    return hashlib.sha256(p.encode()).hexdigest()


# ---------------------------------------------------------------- template helpers
@app.template_filter("fmt")
def fmt(v):
    if v is None:
        return ""
    if isinstance(v, timedelta):
        s = int(v.total_seconds())
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}"
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, date):
        return v.isoformat()
    return v


@app.context_processor
def inject_globals():
    return dict(APPT_STATUSES=APPT_STATUSES, today=date.today().isoformat())


def login_required(role=None):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            if "role" not in session:
                return redirect(url_for("login"))
            if role and session["role"] != role:
                abort(403)
            return f(*a, **k)
        return wrapper
    return deco


def is_worker():
    return session.get("role") == "worker"


# ---------------------------------------------------------------- authentication
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "resident")
        username = request.form.get("username", "").strip()
        pw = hash_pw(request.form.get("password", ""))
        if role == "worker":
            u = q("SELECT worker_id AS uid, full_name, status FROM Health_Workers "
                  "WHERE username=%s AND password_hash=%s", (username, pw), one=True)
            if u and u["status"] != "Active":
                flash("This health worker account is inactive.", "error")
                return render_template("login.html")
        else:
            u = q("SELECT resident_id AS uid, full_name FROM Residents "
                  "WHERE username=%s AND password_hash=%s", (username, pw), one=True)
        if u:
            session.clear()
            session.update(role=role, uid=u["uid"], name=u["full_name"])
            return redirect(url_for("dashboard"))
        flash("Wrong username or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        if len(f.get("password", "")) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            n = run("INSERT INTO Residents (full_name, birth_date, contact_number, address, username, password_hash) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (f["full_name"].strip(), f["birth_date"], f["contact_number"].strip(),
                     f["address"].strip(), f["username"].strip(), hash_pw(f["password"])),
                    "Account created. You can log in now.")
            if n is not None:
                return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- dashboard
@app.route("/")
@login_required()
def dashboard():
    news = q("SELECT title, date_posted FROM Announcements ORDER BY date_posted DESC LIMIT 3")
    if is_worker():
        stats = dict(
            residents=q("SELECT COUNT(*) AS n FROM Residents", one=True)["n"],
            pending=q("SELECT COUNT(*) AS n FROM Appointments WHERE status='Pending'", one=True)["n"],
            lowstock=q("SELECT COUNT(*) AS n FROM Medicines WHERE availability_status<>'Available'", one=True)["n"],
            programs=q("SELECT COUNT(*) AS n FROM Health_Programs WHERE status='Upcoming'", one=True)["n"],
        )
        return render_template("dashboard.html", stats=stats, news=news, upcoming=[])
    upcoming = q("SELECT * FROM vw_appointment_details WHERE resident_id=%s AND status IN ('Pending','Approved') "
                 "AND appointment_date>=CURDATE() ORDER BY appointment_date, start_time LIMIT 5", (session["uid"],))
    return render_template("dashboard.html", stats=None, news=news, upcoming=upcoming)


# ---------------------------------------------------------------- appointments
@app.route("/appointments")
@login_required()
def appointments():
    status = request.args.get("status", "")
    if is_worker():
        if status:
            rows = q("SELECT * FROM vw_appointment_details WHERE status=%s ORDER BY appointment_date DESC, start_time", (status,))
        else:
            rows = q("SELECT * FROM vw_appointment_details ORDER BY appointment_date DESC, start_time")
    else:
        rows = q("SELECT * FROM vw_appointment_details WHERE resident_id=%s ORDER BY appointment_date DESC, start_time",
                 (session["uid"],))
    return render_template("appointments.html", rows=rows, status=status)


@app.route("/appointments/new", methods=["GET", "POST"])
@login_required("resident")
def appt_new():
    workers = q("SELECT worker_id, full_name, position FROM Health_Workers WHERE status='Active' ORDER BY full_name")
    v = request.values
    taken = []
    if v.get("worker_id") and v.get("date"):
        taken = [t["start_time"] for t in q(
            "SELECT start_time FROM Appointments WHERE worker_id=%s AND appointment_date=%s AND status IN ('Pending','Approved')",
            (v["worker_id"], v["date"]))]
        taken = [fmt(t) for t in taken]
    if request.method == "POST" and "book" in request.form:
        f = request.form
        reason = f.get("reason", "").strip()
        try:
            d = date.fromisoformat(f.get("date", ""))
        except ValueError:
            d = None
        if not (reason and d and f.get("start") and f.get("worker_id")):
            flash("Please complete all fields.", "error")
        elif d < date.today():
            flash("Please choose today or a future date.", "error")
        else:
            end = (datetime.strptime(f["start"], "%H:%M") + timedelta(minutes=30)).strftime("%H:%M")
            n = run("INSERT INTO Appointments (appointment_date, start_time, end_time, reason, status, resident_id, worker_id) "
                    "VALUES (%s,%s,%s,%s,'Pending',%s,%s)",
                    (d, f["start"] + ":00", end + ":00", reason, session["uid"], f["worker_id"]),
                    "Appointment requested. Status: Pending.")
            if n is not None:
                return redirect(url_for("appointments"))
    return render_template("appointment_new.html", workers=workers, slots=SLOTS, taken=taken, v=v)


@app.route("/appointments/<int:aid>/cancel", methods=["POST"])
@login_required("resident")
def appt_cancel(aid):
    n = run("UPDATE Appointments SET status='Cancelled' WHERE appointment_id=%s AND resident_id=%s "
            "AND status IN ('Pending','Approved')", (aid, session["uid"]))
    if n:
        flash("Appointment cancelled.", "ok")
    elif n == 0:
        flash("This appointment can no longer be cancelled.", "error")
    return redirect(url_for("appointments"))


@app.route("/appointments/<int:aid>/status", methods=["POST"])
@login_required("worker")
def appt_status(aid):
    s = request.form.get("status")
    if s in APPT_STATUSES:
        run("UPDATE Appointments SET status=%s WHERE appointment_id=%s", (s, aid), f"Appointment marked {s}.")
    return redirect(request.referrer or url_for("appointments"))


@app.route("/appointments/<int:aid>/delete", methods=["POST"])
@login_required("worker")
def appt_delete(aid):
    run("DELETE FROM Appointments WHERE appointment_id=%s", (aid,), "Appointment deleted.")
    return redirect(url_for("appointments"))


# ---------------------------------------------------------------- residents (worker CRUD)
@app.route("/residents")
@login_required("worker")
def residents():
    rows = q("SELECT resident_id, full_name, birth_date, contact_number, address, created_at FROM Residents ORDER BY full_name")
    return render_template("residents.html", rows=rows)


@app.route("/residents/new", methods=["GET", "POST"])
@login_required("worker")
def resident_new():
    if request.method == "POST":
        f = request.form
        n = run("INSERT INTO Residents (full_name, birth_date, contact_number, address, username, password_hash) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (f["full_name"].strip(), f["birth_date"], f["contact_number"].strip(), f["address"].strip(),
                 f["username"].strip(), hash_pw(f["password"] or "password123")), "Resident added.")
        if n is not None:
            return redirect(url_for("residents"))
    return render_template("resident_form.html", r=None)


@app.route("/residents/<int:rid>/edit", methods=["GET", "POST"])
@login_required("worker")
def resident_edit(rid):
    r = q("SELECT * FROM Residents WHERE resident_id=%s", (rid,), one=True)
    if not r:
        abort(404)
    if request.method == "POST":
        f = request.form
        n = run("UPDATE Residents SET full_name=%s, birth_date=%s, contact_number=%s, address=%s WHERE resident_id=%s",
                (f["full_name"].strip(), f["birth_date"], f["contact_number"].strip(), f["address"].strip(), rid),
                "Resident updated.")
        if n is not None:
            if f.get("password"):
                run("UPDATE Residents SET password_hash=%s WHERE resident_id=%s", (hash_pw(f["password"]), rid))
            return redirect(url_for("residents"))
    return render_template("resident_form.html", r=r)


@app.route("/residents/<int:rid>/delete", methods=["POST"])
@login_required("worker")
def resident_delete(rid):
    run("DELETE FROM Residents WHERE resident_id=%s", (rid,), "Resident deleted.")
    return redirect(url_for("residents"))


# ---------------------------------------------------------------- medical records and prescriptions
@app.route("/records")
@login_required()
def records():
    sql = ("SELECT mr.record_id, mr.visit_date, r.full_name AS resident, mr.diagnosis, mr.notes, w.full_name AS health_worker "
           "FROM Medical_Records mr JOIN Residents r ON r.resident_id=mr.resident_id "
           "JOIN Health_Workers w ON w.worker_id=mr.worker_id ")
    if is_worker():
        rows = q(sql + "ORDER BY mr.visit_date DESC")
    else:
        rows = q(sql + "WHERE mr.resident_id=%s ORDER BY mr.visit_date DESC", (session["uid"],))
    return render_template("records.html", rows=rows)


@app.route("/records/new", methods=["GET", "POST"])
@login_required("worker")
def record_new():
    if request.method == "POST":
        f = request.form
        n = run("INSERT INTO Medical_Records (visit_date, diagnosis, notes, resident_id, worker_id) VALUES (%s,%s,%s,%s,%s)",
                (f["visit_date"], f["diagnosis"].strip(), f["notes"].strip(), f["resident_id"], session["uid"]),
                "Medical record saved.")
        if n is not None:
            return redirect(url_for("records"))
    res = q("SELECT resident_id, full_name FROM Residents ORDER BY full_name")
    return render_template("record_new.html", residents=res)


@app.route("/prescriptions")
@login_required()
def prescriptions():
    sql = ("SELECT p.prescription_id, p.prescribed_at, r.full_name AS resident, m.medicine_name AS medicine, "
           "p.quantity, p.instructions, mr.diagnosis, w.full_name AS prescribed_by "
           "FROM Prescriptions p JOIN Residents r ON r.resident_id=p.resident_id "
           "JOIN Medicines m ON m.medicine_id=p.medicine_id "
           "JOIN Medical_Records mr ON mr.record_id=p.record_id "
           "JOIN Health_Workers w ON w.worker_id=p.worker_id ")
    if is_worker():
        rows = q(sql + "ORDER BY p.prescribed_at DESC")
    else:
        rows = q(sql + "WHERE p.resident_id=%s ORDER BY p.prescribed_at DESC", (session["uid"],))
    return render_template("prescriptions.html", rows=rows)


@app.route("/prescriptions/new", methods=["GET", "POST"])
@login_required("worker")
def prescription_new():
    if request.method == "POST":
        f = request.form
        try:
            qty = int(f["quantity"])
        except ValueError:
            flash("Quantity must be a whole number.", "error")
            qty = None
        rec = q("SELECT resident_id FROM Medical_Records WHERE record_id=%s", (f.get("record_id"),), one=True)
        if qty is not None and rec:
            db = get_db()
            try:  # TRANSACTION: save the prescription AND reduce stock, or do neither
                with db.cursor() as cur:
                    cur.execute("INSERT INTO Prescriptions (quantity, instructions, resident_id, worker_id, medicine_id, record_id) "
                                "VALUES (%s,%s,%s,%s,%s,%s)",
                                (qty, f["instructions"].strip(), rec["resident_id"], session["uid"], f["medicine_id"], f["record_id"]))
                    cur.execute("UPDATE Medicines SET quantity = quantity - %s WHERE medicine_id=%s", (qty, f["medicine_id"]))
                db.commit()
                flash("Prescription saved and medicine stock reduced.", "ok")
                return redirect(url_for("prescriptions"))
            except pymysql.MySQLError as e:
                db.rollback()
                flash(db_error(e) + " Nothing was saved.", "error")
    recs = q("SELECT mr.record_id, mr.visit_date, mr.diagnosis, r.full_name FROM Medical_Records mr "
             "JOIN Residents r ON r.resident_id=mr.resident_id ORDER BY mr.visit_date DESC")
    meds = q("SELECT medicine_id, medicine_name, quantity FROM Medicines ORDER BY medicine_name")
    return render_template("prescription_new.html", recs=recs, meds=meds)


# ---------------------------------------------------------------- medicines
@app.route("/medicines")
@login_required()
def medicines():
    rows = q("SELECT * FROM Medicines ORDER BY medicine_name")
    return render_template("medicines.html", rows=rows)


@app.route("/medicines/add", methods=["POST"])
@login_required("worker")
def medicine_add():
    f = request.form
    run("INSERT INTO Medicines (medicine_name, category, quantity, availability_status) VALUES (%s,%s,%s,'Out of Stock')",
        (f["medicine_name"].strip(), f["category"].strip(), f["quantity"] or 0), "Medicine added.")
    return redirect(url_for("medicines"))


@app.route("/medicines/<int:mid>/update", methods=["POST"])
@login_required("worker")
def medicine_update(mid):
    run("UPDATE Medicines SET quantity=%s WHERE medicine_id=%s", (request.form["quantity"], mid), "Stock updated.")
    return redirect(url_for("medicines"))


@app.route("/medicines/<int:mid>/delete", methods=["POST"])
@login_required("worker")
def medicine_delete(mid):
    run("DELETE FROM Medicines WHERE medicine_id=%s", (mid,), "Medicine deleted.")
    return redirect(url_for("medicines"))


# ---------------------------------------------------------------- health programs
@app.route("/programs")
@login_required()
def programs():
    rid = 0 if is_worker() else session["uid"]
    rows = q("SELECT hp.program_id, hp.program_name, hp.description, hp.schedule, hp.status, w.full_name AS worker, "
             "pr.status AS reg_status FROM Health_Programs hp JOIN Health_Workers w ON w.worker_id=hp.worker_id "
             "LEFT JOIN Program_Registrations pr ON pr.program_id=hp.program_id AND pr.resident_id=%s "
             "ORDER BY hp.schedule", (rid,))
    return render_template("programs.html", rows=rows, statuses=PROGRAM_STATUSES)


@app.route("/programs/add", methods=["POST"])
@login_required("worker")
def program_add():
    f = request.form
    run("INSERT INTO Health_Programs (program_name, description, schedule, status, worker_id) VALUES (%s,%s,%s,'Upcoming',%s)",
        (f["program_name"].strip(), f["description"].strip(), f["schedule"].replace("T", " "), session["uid"]),
        "Program created.")
    return redirect(url_for("programs"))


@app.route("/programs/<int:pid>/status", methods=["POST"])
@login_required("worker")
def program_status(pid):
    s = request.form.get("status")
    if s in PROGRAM_STATUSES:
        run("UPDATE Health_Programs SET status=%s WHERE program_id=%s", (s, pid), "Program updated.")
    return redirect(url_for("programs"))


@app.route("/programs/<int:pid>/delete", methods=["POST"])
@login_required("worker")
def program_delete(pid):
    run("DELETE FROM Health_Programs WHERE program_id=%s", (pid,), "Program deleted.")
    return redirect(url_for("programs"))


@app.route("/programs/<int:pid>/register", methods=["POST"])
@login_required("resident")
def program_register(pid):
    prog = q("SELECT status FROM Health_Programs WHERE program_id=%s", (pid,), one=True)
    if not prog or prog["status"] != "Upcoming":
        flash("You can only register for upcoming programs.", "error")
        return redirect(url_for("programs"))
    old = q("SELECT status FROM Program_Registrations WHERE resident_id=%s AND program_id=%s", (session["uid"], pid), one=True)
    if old and old["status"] == "Cancelled":
        run("UPDATE Program_Registrations SET status='Registered' WHERE resident_id=%s AND program_id=%s",
            (session["uid"], pid), "You are registered again.")
    else:  # if a duplicate exists, the UNIQUE constraint rejects it and the message is shown
        run("INSERT INTO Program_Registrations (resident_id, program_id, status) VALUES (%s,%s,'Registered')",
            (session["uid"], pid), "Registered for the program.")
    return redirect(url_for("programs"))


@app.route("/programs/<int:pid>/unregister", methods=["POST"])
@login_required("resident")
def program_unregister(pid):
    run("UPDATE Program_Registrations SET status='Cancelled' WHERE resident_id=%s AND program_id=%s AND status='Registered'",
        (session["uid"], pid), "Registration cancelled.")
    return redirect(url_for("programs"))


@app.route("/registrations")
@login_required("worker")
def registrations():
    rows = q("SELECT pr.registration_id, r.full_name AS resident, hp.program_name, pr.registered_at, pr.status "
             "FROM Program_Registrations pr JOIN Residents r ON r.resident_id=pr.resident_id "
             "JOIN Health_Programs hp ON hp.program_id=pr.program_id ORDER BY pr.registered_at DESC")
    return render_template("registrations.html", rows=rows, statuses=REG_STATUSES)


@app.route("/registrations/<int:rid>/status", methods=["POST"])
@login_required("worker")
def registration_status(rid):
    s = request.form.get("status")
    if s in REG_STATUSES:
        run("UPDATE Program_Registrations SET status=%s WHERE registration_id=%s", (s, rid), "Registration updated.")
    return redirect(url_for("registrations"))


# ---------------------------------------------------------------- announcements
@app.route("/announcements")
@login_required()
def announcements():
    rows = q("SELECT a.announcement_id, a.title, a.content, a.date_posted, w.full_name AS posted_by "
             "FROM Announcements a JOIN Health_Workers w ON w.worker_id=a.worker_id ORDER BY a.date_posted DESC")
    return render_template("announcements.html", rows=rows)


@app.route("/announcements/add", methods=["POST"])
@login_required("worker")
def announcement_add():
    f = request.form
    run("INSERT INTO Announcements (title, content, worker_id) VALUES (%s,%s,%s)",
        (f["title"].strip(), f["content"].strip(), session["uid"]), "Announcement posted.")
    return redirect(url_for("announcements"))


@app.route("/announcements/<int:aid>/edit", methods=["GET", "POST"])
@login_required("worker")
def announcement_edit(aid):
    a = q("SELECT * FROM Announcements WHERE announcement_id=%s", (aid,), one=True)
    if not a:
        abort(404)
    if request.method == "POST":
        f = request.form
        n = run("UPDATE Announcements SET title=%s, content=%s WHERE announcement_id=%s",
                (f["title"].strip(), f["content"].strip(), aid), "Announcement updated.")
        if n is not None:
            return redirect(url_for("announcements"))
    return render_template("announcement_form.html", a=a)


@app.route("/announcements/<int:aid>/delete", methods=["POST"])
@login_required("worker")
def announcement_delete(aid):
    run("DELETE FROM Announcements WHERE announcement_id=%s", (aid,), "Announcement deleted.")
    return redirect(url_for("announcements"))


# ---------------------------------------------------------------- reports (required queries)
REPORTS = [
    ("Multi-table join: prescriptions with resident, worker, medicine, diagnosis",
     "SELECT p.prescription_id, r.full_name AS resident, w.full_name AS prescribed_by, m.medicine_name, p.quantity, mr.diagnosis\n"
     "FROM Prescriptions p\nJOIN Residents r ON r.resident_id = p.resident_id\nJOIN Health_Workers w ON w.worker_id = p.worker_id\n"
     "JOIN Medicines m ON m.medicine_id = p.medicine_id\nJOIN Medical_Records mr ON mr.record_id = p.record_id\n"
     "ORDER BY p.prescription_id LIMIT 15"),
    ("GROUP BY + HAVING: workers with more than 1 appointment",
     "SELECT w.worker_id, w.full_name, COUNT(*) AS total_appointments\nFROM Appointments a\nJOIN Health_Workers w ON w.worker_id = a.worker_id\n"
     "GROUP BY w.worker_id, w.full_name\nHAVING COUNT(*) > 1\nORDER BY total_appointments DESC"),
    ("Subquery: residents who never requested an appointment",
     "SELECT resident_id, full_name\nFROM Residents\nWHERE resident_id NOT IN (SELECT resident_id FROM Appointments)\nLIMIT 15"),
    ("Subquery: medicines with stock below the average",
     "SELECT medicine_name, quantity\nFROM Medicines\nWHERE quantity < (SELECT AVG(quantity) FROM Medicines)\nORDER BY quantity"),
    ("View: pending appointments (vw_appointment_details)",
     "SELECT appointment_id, appointment_date, start_time, resident_name, worker_name, status\nFROM vw_appointment_details\n"
     "WHERE status = 'Pending'\nORDER BY appointment_date"),
]


@app.route("/reports")
@login_required("worker")
def reports():
    out = []
    for title, sql in REPORTS:
        try:
            out.append((title, sql, q(sql), None))
        except pymysql.MySQLError as e:
            out.append((title, sql, [], db_error(e)))
    return render_template("reports.html", reports=out)


# ---------------------------------------------------------------- constraint tests (every one should be blocked)
TESTS = [
    ("Double booking (UNIQUE uq_worker_slot)",
     "INSERT INTO Appointments (appointment_date, start_time, end_time, reason, resident_id, worker_id) "
     "SELECT appointment_date, start_time, end_time, 'Double booking test', 2, worker_id FROM Appointments LIMIT 1"),
    ("End time before start time (CHECK chk_appt_time)",
     "INSERT INTO Appointments (appointment_date, start_time, end_time, reason, resident_id, worker_id) "
     "VALUES ('2030-01-10','10:00:00','09:00:00','Bad time test',1,1)"),
    ("Prescription above stock (trigger trg_presc_check_bi)",
     "INSERT INTO Prescriptions (quantity, instructions, resident_id, worker_id, medicine_id, record_id) "
     "SELECT 99999,'Stock test',mr.resident_id,mr.worker_id,m.medicine_id,mr.record_id FROM Medical_Records mr, Medicines m LIMIT 1"),
    ("Appointment with an inactive worker (trigger trg_appt_worker_active_bi)",
     "INSERT INTO Appointments (appointment_date, start_time, end_time, reason, resident_id, worker_id) "
     "VALUES ('2030-01-10','10:00:00','10:30:00','Inactive worker test',1,(SELECT worker_id FROM Health_Workers WHERE status='Inactive' LIMIT 1))"),
    ("Duplicate program registration (UNIQUE uq_resident_program)",
     "INSERT INTO Program_Registrations (resident_id, program_id) SELECT resident_id, program_id FROM Program_Registrations LIMIT 1"),
    ("Negative medicine quantity (CHECK chk_medicine_qty)",
     "UPDATE Medicines SET quantity = -5 WHERE medicine_id = 1"),
    ("Delete a resident that has appointments (FOREIGN KEY RESTRICT)",
     "DELETE FROM Residents WHERE resident_id = (SELECT resident_id FROM Appointments LIMIT 1)"),
    ("Invalid contact number (CHECK chk_resident_contact)",
     "UPDATE Residents SET contact_number = '123' WHERE resident_id = 1"),
    ("Birth date in the future (trigger trg_resident_birth_bi)",
     "INSERT INTO Residents (full_name, birth_date, contact_number, address, username, password_hash) "
     "VALUES ('Future Test','2099-01-01','09999999999','Test','future_test','x')"),
]


@app.route("/constraints", methods=["GET", "POST"])
@login_required("worker")
def constraints():
    results = {}
    if request.method == "POST":
        pick = request.form.get("test")
        idxs = range(len(TESTS)) if pick == "all" else [int(pick)]
        db = get_db()
        for i in idxs:
            try:
                with db.cursor() as cur:
                    cur.execute(TESTS[i][1])
                db.rollback()  # never keep test data
                results[i] = (False, "NOT blocked: the database accepted it (rolled back).")
            except pymysql.MySQLError as e:
                db.rollback()
                results[i] = (True, db_error(e))
    return render_template("constraints.html", tests=TESTS, results=results)


if __name__ == "__main__":
    app.run(debug=True)
