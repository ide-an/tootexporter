from mastodon import Mastodon
import db as dbpkg
from rq import Queue
from worker import conn
import json
from datetime import datetime
from time import sleep
import traceback
import tempfile
import os.path as path
import shutil

q = Queue(connection=conn)

def get_mastodon(access_token=None):
    return Mastodon(
        client_id = 'client.secret',
        access_token = access_token,
        api_base_url = 'https://gensokyo.cloud'
    )

def reserve_snapshot(user_id, snap_type):
    db = dbpkg.Db()
    snapshot_id = db.add_snapshot(user_id, snap_type)
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
        if snapshot['snap_type'] == dbpkg.SNAPSHOT_TYPE_TOOT:
            page = m.account_statuses(owner['mastodon_id'], limit=100)
        elif snapshot['snap_type'] == dbpkg.SNAPSHOT_TYPE_FAV:
            page = m.favourites(limit=100)
        else:
            raise ValueError('invalid snap_type: {0}'.format(snapshot['snap_type']))
        if page is not None:
            toots += page
            #while True:
            for i in range(10):
                page = m.fetch_next(page)
                if page is None:
                    break
                toots += page
                sleep(1)
        # TODO: generate html
        archive = save_local(toots)
        print(archive)
        # TODO: save to S3
        db.update_snapshot(snapshot_id, {'status': dbpkg.SNAPSHOT_STATUS_DONE})
    except Exception as e:
        print('snapshot failed: {0}'.format(snapshot_id))
        print(traceback.format_exc())
        try:
            db.update_snapshot(snapshot_id, {'status': dbpkg.SNAPSHOT_STATUS_FAIL})
        except Exception as e:
            print('snapshot failed: {0}'.format(snapshot_id))
            print(traceback.format_exc())

def save_local(toots):
    '''
    return path to archive
    '''
    tmpdir = tempfile.mkdtemp()
    with open(path.join(tmpdir, 'index.html'), 'w') as f:
        f.write('''
<!doctype html>
<script>
var toots = 
        ''')
        f.write(json.dumps(toots, default=json_default))
        f.write('''
</script>
        ''')
    return shutil.make_archive("save", "zip", tmpdir)

# datetimeがjson serializableじゃないので変換を定義する
def json_default(o):
    # See https://qiita.com/podhmo/items/dc748a9d40026c28556d
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(repr(o) + ' is not JSON serializable')
