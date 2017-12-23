# tootexporter

gensokyo.cloudの投稿サルベージツール

## Herokuへのデプロイ


## 開発環境セットアップ

vagrantを使用する。
```bash
cp .env.sample .env
# .envを編集する
vagrant up
vagrant ssh -c 'cd tootexporter/ && foreman start -f Procfile.dev'
```

## 設定系(.envファイル)
