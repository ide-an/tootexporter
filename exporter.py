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
import boto3
import os

q = Queue(connection=conn)

def get_mastodon(access_token=None):
    return Mastodon(
        client_id = os.environ['MASTODON_CLIENT_ID'],
        client_secret = os.environ['MASTODON_CLIENT_SECRET'],
        access_token = access_token,
        api_base_url = os.environ['MASTODON_API_BASE']
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
        # collect all toots
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
        # save toots to AWS S3
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = save_local(toots, tmpdir)
            bucket = os.environ['S3_BUCKET']
            key = 'archive/toots_{0}.zip'.format(snapshot_id)
            save_remote(archive, bucket, key)
        print(archive)
        db.update_snapshot(snapshot_id, {
            'status': dbpkg.SNAPSHOT_STATUS_DONE,
            'bucket': bucket,
            'key': key,
        })
    except Exception as e:
        print('snapshot failed: {0}'.format(snapshot_id))
        print(traceback.format_exc())
        try:
            db.update_snapshot(snapshot_id, {'status': dbpkg.SNAPSHOT_STATUS_FAIL})
        except Exception as e:
            print('snapshot failed: {0}'.format(snapshot_id))
            print(traceback.format_exc())

def save_local(toots, tmpdir):
    '''
    return path to archive
    '''
    archive_root = path.join(tmpdir, 'archive')
    shutil.copytree('archive_assets/', archive_root)
    with open(path.join(archive_root, 'toots.js'), 'w') as f:
        f.write('var toots = \n')
        f.write(json.dumps(toots, default=json_default))
    return shutil.make_archive(path.join(tmpdir, 'toots'), "zip", archive_root)

def save_remote(archive_path, bucket, key):
    '''
    save archive to AWS S3
    '''
    s3 = boto3.client('s3')
    with open(archive_path, 'rb') as data:
        s3.upload_fileobj(data, bucket, key)

def generate_download_url(bucket, key):
    '''
    generate download url for saved archive in AWS S3
    generated url expires in 24hours
    '''
    s3 = boto3.client('s3')
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': key,
        },
        ExpiresIn = 60*60*24
    )

# datetimeがjson serializableじゃないので変換を定義する
def json_default(o):
    # See https://qiita.com/podhmo/items/dc748a9d40026c28556d
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(repr(o) + ' is not JSON serializable')
