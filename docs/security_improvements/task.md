# セキュリティ改善タスク

- [x] バックエンド (app.py) の修正
  - [x] APIキー認証の追加
  - [x] CSRF対策の強化
  - [x] 入力値の長さ制限設定
  - [x] レート制限 (flask-limiter) の追加
  - [x] セキュリティヘッダーの設定
  - [x] デバッグモードOFF
- [x] requirements.txt に flask-limiter を追加
- [x] フロントエンドの修正
  - [x] index.html にCSRFトークン用metaタグとログインUIを追加
  - [x] app.js でAPIキーとCSRFトークンをリクエストに含める処理を追加
- [x] デプロイ設定の修正
  - [x] render.yaml に環境変数設定を追加
