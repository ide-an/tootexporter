from flask import g
import os
from urllib import parse
import psycopg2
import psycopg2.extras
from datetime import datetime

SNAPSHOT_STATUS_WAIT = "wait"
SNAPSHOT_STATUS_DOING = "doing"
SNAPSHOT_STATUS_DONE = "done"
SNAPSHOT_STATUS_FAIL = "fail"

def get_db():
    if not hasattr(g, "db"):
        parse.uses_netloc.append("postgres")
        url = parse.urlparse(os.environ["DATABASE_URL"])
        g.db = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    return g.db

def close_db():
    if hasattr(g, 'db'):
        g.db.close()

def add_or_create_user(access_token, user):
    now = datetime.now()
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE mastodon_id = %(mastodon_id)s;", {"mastodon_id": user["id"]})
            res = cur.fetchone()
            if res is None:# create user
                cur.execute("INSERT INTO users (access_token, mastodon_id, created_at, updated_at) VALUES (%(access_token)s, %(mastodon_id)s, %(created_at)s, %(updated_at)s)",
                            {
                                "access_token": access_token,
                                "mastodon_id": user["id"],
                                "created_at": now,
                                "updated_at": now,
                            })
            else:
                cur.execute("UPDATE users SET access_token = %(access_token)s, updated_at = %(updated_at)s WHERE mastodon_id = %(mastodon_id)s",
                            {
                                "access_token": access_token,
                                "mastodon_id": user["id"],
                                "updated_at": now,
                            })
def get_user_by_mastodon_id(mastodon_id):
    with get_db() as db:
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE mastodon_id = %s;", (mastodon_id,))
            return  cur.fetchone()

def add_snapshot(user_id, snap_type, snap_start, snap_end):
    now = datetime.now()
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute("INSERT INTO snapshots (owner, snap_type, snap_start, snap_end, status, created_at, updated_at) VALUES "
                        + "(%(owner)s, %(snap_type)s, %(snap_start)s, %(snap_end)s, %(status)s, %(created_at)s, %(updated_at)s)",
                        {
                            "owner": user_id,
                            "snap_type": snap_type,
                            "snap_start": snap_start,
                            "snap_end" : snap_end,
                            "created_at": now,
                            "updated_at": now,
                            "status": SNAPSHOT_STATUS_WAIT,
                        })

def get_snapshot(id):
    with get_db() as db:
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM snapshots WHERE id = %s;", (id,))
            return  cur.fetchone()

def get_snapshots_by_owner(user_id):
    with get_db() as db:
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM snapshots WHERE owner = %s;", (user_id,))
            return  cur.fetchall()

def update_snapshot(id, values):
    """
    id: snapshot id
    values: dict of columname and valu to update
    """
# generate sql statement
    now = datetime.now()
    sql_values = {
        "id": id,
        "updated_at": now,
    }
    set_exprs = [
        "updated_at = %(updated_at)s",
    ]
    for k,v in enumerate(values):
        set_exprs.append(k + " = %(" + k + ")s")
        sql_values[k] = v
    sql = "UPDATE snapshot SET " + ", ".join(set_exprs) + " WHERE id = %(id)s"
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(sql, sql_values)
