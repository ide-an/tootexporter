from mastodon import Mastodon
import db as dbpkg
from rq import Queue
from worker import conn
import json
from datetime import datetime
from time import sleep
import traceback

q = Queue(connection=conn)

def get_mastodon(access_token=None):
    return Mastodon(
        client_id = 'client.secret',
        access_token = access_token,
        api_base_url = 'https://gensokyo.cloud'
    )

def reserve_snapshot(user_id, snap_type, snap_start, snap_end):
    db = dbpkg.Db()
    snapshot_id = db.add_snapshot(user_id, snap_type, snap_start, snap_end)
    q.enqueue(export_toots,snapshot_id)

def export_toots(snapshot_id):
    try:
        db = dbpkg.Db()
        snapshot = db.get_snapshot(snapshot_id)
        owner = db.get_user(snapshot['owner'])
        db.update_snapshot(snapshot_id, {'status': dbpkg.SNAPSHOT_STATUS_DOING})
        m = get_mastodon(access_token = owner['access_token'])
        print(snapshot)
        toots = []
        page = m.account_statuses(owner['mastodon_id'], limit=100)
        if page is not None:
            toots += page
            for i in range(10):
                page = m.fetch_next(page)
                if page is None:
                    break
                toots += page
                # TODO: check snap_start and snap_end
                sleep(1)
        with open("snap_{0}.json".format(snapshot_id), "w") as f:
            json.dump(toots, f, default=json_default, indent=2)
        # TODO: generate html
        # TODO: save to S3
        db.update_snapshot(snapshot_id, {'status': dbpkg.SNAPSHOT_STATUS_DONE})
    except Exception as e:
        print("snapshot failed: {0}".format(snapshot_id))
        print(traceback.format_exc())
        try:
            db.update_snapshot(snapshot_id, {'status': dbpkg.SNAPSHOT_STATUS_FAIL})
        except Exception as e:
            print("snapshot failed: {0}".format(snapshot_id))
            print(traceback.format_exc())

# datetimeがjson serializableじゃないので変換を定義する
def json_default(o):
    # See https://qiita.com/podhmo/items/dc748a9d40026c28556d
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(repr(o) + " is not JSON serializable")
