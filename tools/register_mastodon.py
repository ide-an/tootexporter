from mastodon import Mastodon
import os

client_id, client_secret = Mastodon.create_app(
    'tootexporter',
    redirect_uris = os.environ['OAUTH_CALLBACK_URL'],
    api_base_url = os.environ['MASTODON_API_BASE']
)
print("""
MASTODON_CLIENT_ID={0}
MASTODON_CLIENT_SECRET={1}
""".format(client_id, client_secret)
      )
