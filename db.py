import os
from urllib import parse
import psycopg2
import psycopg2.extras
from datetime import datetime

SNAPSHOT_STATUS_WAIT = "wait"
SNAPSHOT_STATUS_DOING = "doing"
SNAPSHOT_STATUS_DONE = "done"
SNAPSHOT_STATUS_FAIL = "fail"

SNAPSHOT_TYPE_TOOT = "toot"
SNAPSHOT_TYPE_FAV = "fav"

class Db:
    db = None
    def get_db(self,):
        if self.db is None:
            parse.uses_netloc.append("postgres")
            url = parse.urlparse(os.environ["DATABASE_URL"])
            self.db = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
        return self.db

    def close_db(self,):
        if self.db is not None:
            self.db.close()

    def add_or_create_user(self,access_token, user):
        now = datetime.now()
        with self.get_db() as db:
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
    def get_user_by_mastodon_id(self,mastodon_id):
        with self.get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE mastodon_id = %s;", (mastodon_id,))
                return  cur.fetchone()

    def get_user(self,id):
        with self.get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE id = %s;", (id,))
                return  cur.fetchone()

    def add_snapshot(self,user_id, snap_type):
        """
        add snapshot and return snapshot.id
        """
        now = datetime.now()
        with self.get_db() as db:
            with db.cursor() as cur:
                cur.execute("INSERT INTO snapshots (owner, snap_type, status, created_at, updated_at) VALUES "
                            + "(%(owner)s, %(snap_type)s, %(status)s, %(created_at)s, %(updated_at)s) RETURNING id",
                            {
                                "owner": user_id,
                                "snap_type": snap_type,
                                "created_at": now,
                                "updated_at": now,
                                "status": SNAPSHOT_STATUS_WAIT,
                            })
                return cur.fetchone()[0]

    def get_snapshot(self,id):
        with self.get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM snapshots WHERE id = %s;", (id,))
                return  cur.fetchone()

    def get_snapshots_by_owner(self,user_id):
        with self.get_db() as db:
            with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM snapshots WHERE owner = %s ORDER BY id;", (user_id,))
                return  cur.fetchall()

    def update_snapshot(self,id, values):
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
        for k,v in values.items():
            set_exprs.append(k + " = %(" + k + ")s")
            sql_values[k] = v
        sql = "UPDATE snapshots SET " + ", ".join(set_exprs) + " WHERE id = %(id)s"
        with self.get_db() as db:
            with db.cursor() as cur:
                cur.execute(sql, sql_values)

    def count_waiting_snapshots(self):
        with self.get_db() as db:
            with db.cursor() as cur:
                cur.execute("SELECT count(*) FROM snapshots WHERE status in ('wait', 'doing');")
                return  cur.fetchone()[0]
