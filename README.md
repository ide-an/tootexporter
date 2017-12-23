# tootexporter

gensokyo.cloudの投稿サルベージツール

## Herokuへのデプロイ

あらかじめAWSでクレデンシャルの作成とS3バケットを作成しておく。

```bash
heroku login
# heroku作成
heroku create
# addon追加
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
# 設定確認。DATABASE_URLとREDIS_URLが表示される
heroku config
# 正しい`OAUTH_CALLBACK_URL`を取得
heroku info -s 2> /dev/null | grep web_url | sed 's#web_url=##' | sed 's#$#callback#'
# mastodonのクレデンシャル取得
OAUTH_CALLBACK_URL=(↑のURL) MASTODON_API_BASE=https://gensokyo.cloud python tools/register_mastodon.py
# .envを作成し、以下の設定を修正
#  * OAUTH_CALLBACK_URL
#  * MASTODON_CLIENT_SECRET
#  * MASTODON_API_BASE
#  * AWS_ACCESS_KEY_ID
#  * AWS_SECRET_ACCESS_KEY
#  * S3_BUCKET
#  * SESSION_SECRET
#  * DATABASE_URL
#  * REDIS_URL
cp .env.sample .env
vi .env
heroku plugins:install heroku-config
heroku config:push
# db初期化
heroku pg:psql  < schema.sql
# push
git push heroku master
heroku scale worker=1
```

## 開発環境セットアップ

vagrantを使用する。
```bash
vagrant up
cp .env.sample .env
# マストドンのclient id/secret取得
vagrant ssh -c 'cd tootexporter/ && export `cat .env` && python3 tools/register_mastodon.py'
# .envを編集する
vi .env
# アプリケーション起動
vagrant ssh -c 'cd tootexporter/ && foreman start -f Procfile.dev'
```

## 設定系(.envファイル)

### 開発環境・本番環境ともに必要な設定
 * `AWS_ACCESS_KEY_ID`
    * AWSのアクセスキー。S3へのトゥート保存などに必要。
 * `AWS_SECRET_ACCESS_KEY`
    * AWSのsecret。S3へのトゥート保存などに必要。
 * `S3_BUCKET`
    * トゥートの保存先のS3バケット。
 * `MASTODON_CLIENT_ID`
    * マストドンのclient id。tools/register_mastodon.pyで取得する。
 * `MASTODON_CLIENT_SECRET`
    * マストドンのclient secret。tools/register_mastodon.pyで取得する。

### 本番で必要な設定
 * `SESSION_SECRET`
    * cookieの暗号化キー。適当に強い乱数を使う。
 * `OAUTH_CALLBACK_URL`
    * OAuth認証するときのリダイレクト先URL。client id/secretを生成するときにも使われ、このときの設定とOAuth認証時でリダイレクト先が違うとエラーになる。
 * `DATABASE_URL`
    * postgresqlのURL。heroku postgresqlを繋げば勝手に設定される。
 * `REDIS_URL`
    * ジョブキューに使うredisのURL。heroku redisを繋げば勝手に設定される。
 * `MASTODON_API_BASE`
    * 対象のマストドンインスタンス。
