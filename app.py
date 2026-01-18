import os, sqlite3, hashlib
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def db(): 
    c = sqlite3.connect("database.db")
    c.row_factory = sqlite3.Row
    return c

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# ===== INIT DB =====
conn = db(); cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE, phone TEXT UNIQUE, password_hash TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS private_messages (
    id INTEGER PRIMARY KEY, sender_id INTEGER, receiver_id INTEGER, message TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
cur.execute("""CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY, name TEXT, owner_id INTEGER)""")
cur.execute("CREATE TABLE IF NOT EXISTS group_members (group_id INTEGER, user_id INTEGER)")
cur.execute("""CREATE TABLE IF NOT EXISTS group_messages (
    id INTEGER PRIMARY KEY, group_id INTEGER, sender_id INTEGER, message TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
conn.commit(); conn.close()

# ===== ROUTES =====
@app.route("/") 
def index(): return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    d = request.json
    try:
        conn = db(); conn.cursor().execute("INSERT INTO users (username, phone, password_hash) VALUES (?,?,?)",
            (d.get("username"), d.get("phone"), hash_pw(d["password"])))
        conn.commit(); conn.close()
        return {"ok": True}
    except sqlite3.IntegrityError: return {"error":"username or phone exists"},400

@app.route("/login", methods=["POST"])
def login():
    d = request.json; c = db()
    row = c.cursor().execute("SELECT id, username, phone FROM users WHERE (username=? OR phone=?) AND password_hash=?",
                              (d.get("login"),d.get("login"),hash_pw(d["password"]))).fetchone()
    c.close()
    return {"user_id": row["id"], "username": row["username"], "phone": row["phone"]} if row else ({"error":"invalid"},401)

@app.route("/search")
def search():
    q = request.args.get("q",""); c = db()
    rows = c.cursor().execute("SELECT id, username FROM users WHERE username LIKE ? LIMIT 20",(f"%{q}%",)).fetchall()
    c.close()
    return jsonify([{"id": r["id"], "username": r["username"]} for r in rows])

@app.route("/dm/send", methods=["POST"])
def send_dm():
    d = request.json; c = db()
    c.cursor().execute("INSERT INTO private_messages (sender_id, receiver_id, message) VALUES (?,?,?)",
                        (d["from"],d["to"],d["msg"]))
    c.commit(); c.close(); return {"sent": True}

@app.route("/dm/history")
def dm_history():
    a,b=request.args["a"],request.args["b"]; c=db()
    rows=c.cursor().execute("SELECT sender_id,message,created_at FROM private_messages WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?) ORDER BY id",(a,b,b,a)).fetchall()
    c.close(); return jsonify([dict(r) for r in rows])

@app.route("/group/create", methods=["POST"])
def create_group():
    d=request.json; c=db()
    c.cursor().execute("INSERT INTO groups (name, owner_id) VALUES (?,?)",(d["name"],d["owner"]))
    gid=c.cursor().execute("SELECT last_insert_rowid()").fetchone()[0]
    c.cursor().execute("INSERT INTO group_members VALUES (?,?)",(gid,d["owner"]))
    c.commit(); c.close(); return {"group_id":gid}

@app.route("/group/send", methods=["POST"])
def group_send():
    d=request.json; c=db()
    c.cursor().execute("INSERT INTO group_messages (group_id,sender_id,message) VALUES (?,?,?)",(d["group"],d["from"],d["msg"]))
    c.commit(); c.close(); return {"sent":True}

@app.route("/group/history")
def group_history():
    gid=request.args["group"]; c=db()
    rows=c.cursor().execute("SELECT sender_id,message,created_at FROM group_messages WHERE group_id=? ORDER BY id",(gid,)).fetchall()
    c.close(); return jsonify([dict(r) for r in rows])

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
