from flask import g
import os
from urllib import parse
import psycopg2
from datetime import datetime

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
            print(res)
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
