import os, hashlib, hmac, base64, secrets, csv, io, logging, json, urllib.request, urllib.error
from html import escape
from db_backend import db, init_postgres_schema, is_integrity_error
from pathlib import Path
from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, Response
from werkzeug.utils import secure_filename

ROOT=Path(__file__).resolve().parent
UPLOADS=ROOT/"static"/"uploads"
UPLOADS.mkdir(exist_ok=True,parents=True)
app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY", "local-development-only-change-before-deploy")
app.config["MAX_CONTENT_LENGTH"]=5*1024*1024
ALLOWED={"jpg","jpeg","png","webp"}


def verify(pw,stored):
 try:
  scheme,rounds,salt,digest=stored.split("$",3)
  if scheme!="pbkdf2_sha256": return False
  dec=lambda s:base64.urlsafe_b64decode(s+"="*(-len(s)%4))
  actual=hashlib.pbkdf2_hmac("sha256",pw.encode(),dec(salt),int(rounds))
  return hmac.compare_digest(actual,dec(digest))
 except Exception: return False

def make_hash(pw):
 rounds=600000; salt=secrets.token_bytes(16)
 dk=hashlib.pbkdf2_hmac("sha256",pw.encode(),salt,rounds)
 enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip("=")
 return f"pbkdf2_sha256${rounds}${enc(salt)}${enc(dk)}"

def user():
 uid=session.get("uid")
 if not uid:return None
 with db() as c:return c.execute("select * from users where id=? and is_active=1",(uid,)).fetchone()

def required(role=None):
 def deco(fn):
  @wraps(fn)
  def wrapped(*a,**kw):
   u=user()
   if not u: flash("Please sign in first.","info"); return redirect(url_for("login"))
   if role and u["role"]!=role: abort(403)
   return fn(*a,**kw)
  return wrapped
 return deco

@app.context_processor
def globals_for_templates(): return {"current_user":user(),"today":date.today().isoformat()}

@app.route("/")
def home(): return redirect(url_for("dashboard") if user() else url_for("login"))

@app.route("/login",methods=["GET","POST"])
def login():
 if user():return redirect(url_for("dashboard"))
 if request.method=="POST":
  email=request.form.get("identity","").strip().lower(); pw=request.form.get("password","")
  with db() as c:u=c.execute("select * from users where lower(email)=lower(?) and is_active=1",(email,)).fetchone()
  if u and verify(pw,u["password_hash"]):
   session.clear();session["uid"]=u["id"]
   return redirect(url_for("admin") if u["role"]=="admin" else url_for("dashboard"))
  flash("Email ID or password is incorrect.","error")
 return render_template("login.html")

@app.post("/logout")
def logout():session.clear();return redirect(url_for("login"))

@app.route("/dashboard")
@required()
def dashboard():
 u=user();q=request.args.get("q","").strip();cat=request.args.get("category","").strip()
 with db() as c:
  sql="""select e.*,(select count(*) from registrations r where r.event_id=e.id) reg_count,
  exists(select 1 from registrations r where r.event_id=e.id and r.user_id=?) joined
  from events e where e.is_published=1 and e.event_date>=?"""
  args=[u["id"],date.today().isoformat()]
  if q:sql+=" and (e.title like ? or e.description like ? or e.venue like ?)";args += [f"%{q}%"]*3
  if cat:sql+=" and e.category=?";args.append(cat)
  sql+=" order by e.event_date,e.event_time"
  events=c.execute(sql,args).fetchall()
  cats=c.execute("select distinct category from events where is_published=1 order by category").fetchall()
  unread=c.execute("select count(*) from notifications where user_id=? and is_read=0",(u["id"],)).fetchone()[0]
 return render_template("dashboard.html",events=events,categories=cats,q=q,selected_category=cat,unread=unread)

@app.route("/event/<int:eid>")
@required()
def event_detail(eid):
 u=user()
 with db() as c:e=c.execute("""select e.*,(select count(*) from registrations r where r.event_id=e.id) reg_count,
 exists(select 1 from registrations r where r.event_id=e.id and r.user_id=?) joined from events e
 where e.id=? and e.is_published=1""",(u["id"],eid)).fetchone()
 if not e:abort(404)
 return render_template("event_detail.html",event=e)

def send_registration_email(student, event):
    """Send a registration confirmation through Brevo's HTTPS API."""
    api_key = os.environ.get("BREVO_API_KEY", "").strip()
    sender_email = os.environ.get("BREVO_SENDER_EMAIL", "").strip()
    sender_name = os.environ.get("BREVO_SENDER_NAME", "SDSF Events").strip()

    if not api_key or not sender_email:
        app.logger.warning(
            "Registration email not sent: BREVO_API_KEY or BREVO_SENDER_EMAIL is not configured."
        )
        return False

    student_name = str(student["name"])
    recipient = str(student["email"])
    title = str(event["title"])
    event_date = str(event["event_date"])
    event_time = str(event["event_time"] or "To be announced")
    venue = str(event["venue"])
    category = str(event["category"])
    description = str(event["description"])

    safe_name = escape(student_name)
    safe_title = escape(title)
    safe_category = escape(category)
    safe_date = escape(event_date)
    safe_time = escape(event_time)
    safe_venue = escape(venue)
    safe_description = escape(description).replace("\n", "<br>")

    text_content = (
        f"Hello {student_name},\n\n"
        f"Your registration for {title} has been confirmed.\n\n"
        "EVENT DETAILS\n"
        f"Event: {title}\nCategory: {category}\nDate: {event_date}\n"
        f"Time: {event_time}\nVenue: {venue}\n\n"
        f"About this event:\n{description}\n\n"
        "You can view your registration by signing in to SDSF Events.\n\n"
        "Regards,\nSDSF Events Team\n"
        "School of Data Science and Forecasting\n"
        "Devi Ahilya Vishwavidyalaya, Indore"
    )

    html_content = f"""<!doctype html>
<html lang="en">
<body style="margin:0;background:#f4f5f8;font-family:Arial,sans-serif;color:#20243a;padding:28px 12px;">
  <div style="max-width:620px;margin:auto;background:#fff;border-radius:18px;overflow:hidden;border:1px solid #e4e6ef;">
    <div style="background:#252078;color:#fff;padding:28px 30px;">
      <div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;opacity:.9;">SDSF · DAVV INDORE</div>
      <h1 style="margin:12px 0 0;font-size:26px;">You're registered!</h1>
      <p style="margin:8px 0 0;color:#e8e7ff;">Your place has been confirmed.</p>
    </div>
    <div style="padding:28px 30px;">
      <p>Hello {safe_name},</p>
      <p>Your registration for <strong>{safe_title}</strong> has been confirmed. We're looking forward to seeing you there.</p>
      <h2 style="font-size:17px;margin:25px 0 12px;">Event details</h2>
      <table role="presentation" style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:9px 0;color:#777;width:110px;">Event</td><td style="padding:9px 0;font-weight:bold;">{safe_title}</td></tr>
        <tr><td style="padding:9px 0;color:#777;">Category</td><td style="padding:9px 0;">{safe_category}</td></tr>
        <tr><td style="padding:9px 0;color:#777;">Date</td><td style="padding:9px 0;">{safe_date}</td></tr>
        <tr><td style="padding:9px 0;color:#777;">Time</td><td style="padding:9px 0;">{safe_time}</td></tr>
        <tr><td style="padding:9px 0;color:#777;">Venue</td><td style="padding:9px 0;">{safe_venue}</td></tr>
      </table>
      <h2 style="font-size:17px;margin:25px 0 10px;">About the event</h2>
      <p style="line-height:1.65;color:#555;">{safe_description}</p>
      <p style="margin-top:26px;">You can view your registration anytime by signing in to SDSF Events.</p>
      <p style="margin-top:28px;">Regards,<br><strong>SDSF Events Team</strong><br>
      <span style="color:#777;font-size:12px;">School of Data Science and Forecasting · Devi Ahilya Vishwavidyalaya, Indore</span></p>
    </div>
  </div>
</body>
</html>"""

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": recipient, "name": student_name}],
        "subject": f"Registration confirmed: {title}",
        "textContent": text_content,
        "htmlContent": html_content,
    }
    request_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=request_data,
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status not in (200, 201, 202):
                app.logger.error("Brevo returned unexpected HTTP status %s.", response.status)
                return False
        return True
    except urllib.error.HTTPError as exc:
        # Do not log request headers or the API key.
        details = exc.read(1000).decode("utf-8", errors="replace")
        app.logger.error("Brevo email request failed (HTTP %s): %s", exc.code, details)
        return False
    except Exception:
        app.logger.exception("Registration saved, but Brevo could not send email to %s.", recipient)
        return False


@app.post("/event/<int:eid>/register")
@required("student")
def register(eid):
    student = user()
    registration_created = False
    event_for_email = None

    with db() as c:
        event = c.execute(
            "SELECT * FROM events WHERE id=? AND is_published=1", (eid,)
        ).fetchone()
        if not event:
            abort(404)

        if event["registration_deadline"] and event["registration_deadline"] < date.today().isoformat():
            flash("Registration is closed.", "error")
        else:
            count = c.execute(
                "SELECT COUNT(*) FROM registrations WHERE event_id=?", (eid,)
            ).fetchone()[0]
            if event["capacity"] and count >= event["capacity"]:
                flash("This event is full.", "error")
            else:
                try:
                    c.execute(
                        "INSERT INTO registrations(event_id,user_id) VALUES(?,?)",
                        (eid, student["id"]),
                    )
                    c.execute(
                        "INSERT INTO notifications(user_id,event_id,title,message) VALUES(?,?,?,?)",
                        (student["id"], eid, "Registration confirmed", f"You are registered for {event['title']}."),
                    )
                    registration_created = True
                    event_for_email = {
                        "title": event["title"],
                        "category": event["category"],
                        "event_date": event["event_date"],
                        "event_time": event["event_time"],
                        "venue": event["venue"],
                        "description": event["description"],
                    }
                except Exception as exc:
                    if not is_integrity_error(exc):
                        raise
                    flash("You are already registered.", "info")

    # The database transaction has committed before attempting email delivery.
    if registration_created:
        if send_registration_email(student, event_for_email):
            flash("Registration confirmed! A confirmation email has been sent to your registered email address.", "success")
        else:
            flash("Registration confirmed! Email delivery is temporarily unavailable; your registration is saved in the portal.", "success")

    return redirect(url_for("event_detail", eid=eid))

@app.route("/notifications")
@required()
def notifications():
 u=user()
 with db() as c:
  rows=c.execute("select * from notifications where user_id=? order by created_at desc",(u["id"],)).fetchall()
  c.execute("update notifications set is_read=1 where user_id=?",(u["id"],))
 return render_template("notifications.html",notifications=rows)

def allowed(name):return "." in name and name.rsplit(".",1)[1].lower() in ALLOWED

@app.route("/admin")
@required("admin")
def admin():
 with db() as c:
  stats={"students":c.execute("select count(*) from users where role='student'").fetchone()[0],
  "events":c.execute("select count(*) from events").fetchone()[0],
  "published":c.execute("select count(*) from events where is_published=1").fetchone()[0],
  "registrations":c.execute("select count(*) from registrations").fetchone()[0]}
  events=c.execute("""select e.*,(select count(*) from registrations r where r.event_id=e.id) reg_count
  from events e order by e.created_at desc""").fetchall()
  students=c.execute("select roll_number,name,email,contact_number from users where role='student' order by roll_number").fetchall()
 return render_template("admin.html",stats=stats,events=events,students=students)

@app.route("/admin/event/new", methods=["GET", "POST"])
@required("admin")
def new_event():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        cat = request.form.get("category", "").strip()
        desc = request.form.get("description", "").strip()
        dt = request.form.get("event_date", "").strip()
        tm = request.form.get("event_time", "").strip()
        venue = request.form.get("venue", "").strip()
        imgurl = request.form.get("image_url", "").strip()
        deadline = request.form.get("registration_deadline", "").strip() or None
        capraw = request.form.get("capacity", "").strip()
        cap = int(capraw) if capraw.isdigit() else None
        published = 1 if request.form.get("is_published") == "on" else 0

        file = request.files.get("image_file")
        if file and file.filename and allowed(file.filename):
            filename = secrets.token_hex(6) + "_" + secure_filename(file.filename)
            file.save(UPLOADS / filename)
            imgurl = url_for("static", filename="uploads/" + filename)

        if not all([title, cat, desc, dt, venue]):
            flash("Complete all required fields.", "error")
            return render_template("event_form.html")

        with db() as c:
            cur = c.execute(
                """
                INSERT INTO events (
                    title, category, description, event_date, event_time,
                    venue, image_url, registration_deadline, capacity,
                    is_published, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    title, cat, desc, dt, tm, venue, imgurl,
                    deadline, cap, published, user()["id"]
                ),
            )
            event_id = cur.fetchone()["id"]

            if published:
                rows = c.execute(
                    "SELECT id FROM users WHERE role='student' AND is_active=1"
                ).fetchall()

                c.executemany(
                    """
                    INSERT INTO notifications(user_id, event_id, title, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    [
                        (
                            row["id"],
                            event_id,
                            "New event announced",
                            f"{title} is now live on the SDSF Events portal.",
                        )
                        for row in rows
                    ],
                )

        flash("Event saved.", "success")
        return redirect(url_for("admin"))

    return render_template("event_form.html")


@app.post("/admin/event/<int:eid>/toggle")
@required("admin")
def toggle(eid):
 with db() as c:
  e=c.execute("select * from events where id=?",(eid,)).fetchone()
  if not e:abort(404)
  status=0 if e["is_published"] else 1;c.execute("update events set is_published=? where id=?",(status,eid))
  if status:
   rows=c.execute("select id from users where role='student' and is_active=1").fetchall()
   c.executemany("insert into notifications(user_id,event_id,title,message) values(?,?,?,?)",
   [(r["id"],eid,"New event announced",f"{e['title']} is now live on the SDSF Events portal.") for r in rows])
 flash("Event visibility updated.","success");return redirect(url_for("admin"))

@app.post("/admin/event/<int:eid>/delete")
@required("admin")
def delete(eid):
 with db() as c:c.execute("delete from events where id=?",(eid,))
 flash("Event deleted.","success");return redirect(url_for("admin"))

@app.get("/admin/students/export")
@required("admin")
def export():
 with db() as c:rows=c.execute("select roll_number,name,email,contact_number from users where role='student' order by roll_number").fetchall()
 out=io.StringIO();w=csv.writer(out);w.writerow(["Roll Number","Name","Email","Contact Number"]);w.writerows([tuple(r) for r in rows])
 return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=sdsf_students.csv"})

@app.errorhandler(403)
def forbidden(e):return render_template("error.html",code=403,message="You do not have permission to view this page."),403
@app.errorhandler(404)
def missing(e):return render_template("error.html",code=404,message="That page could not be found."),404

init_postgres_schema()

if __name__=="__main__":
 app.run(host="127.0.0.1",port=int(os.environ.get("PORT", 5000)),debug=os.environ.get("FLASK_DEBUG") == "1")
