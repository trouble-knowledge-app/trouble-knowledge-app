# セキュリティ脆弱性の調査結果と修正計画

## 発見した脆弱性一覧

| # | 深刻度 | 脆弱性 | 影響 |
|---|--------|--------|------|
| 1 | 🔴 高 | 認証・認可なし | 誰でもデータの閲覧・削除・エクスポートが可能 |
| 2 | 🔴 高 | CSRF保護なし | 悪意あるサイトから記録の作成・削除が可能 |
| 3 | 🟡 中 | 入力値の長さ制限なし | 巨大なデータを送り付けてサーバーを圧迫可能 |
| 4 | 🟡 中 | レート制限なし | API連続呼び出しによるDoS攻撃が可能 |
| 5 | 🟡 中 | セキュリティヘッダー未設定 | クリックジャッキング、MIME Sniffing等のリスク |
| 6 | 🟢 低 | デバッグモードが本番設定に残存 | エラー時に内部情報が漏洩する（現在はgunicornで無効化されているが念のため） |

> [!IMPORTANT]
> **最も重要な脆弱性**は **#1（認証なし）** です。現在URLを知っている人なら誰でも全データにアクセス、削除、エクスポートが可能です。

## 修正方針

> [!NOTE]
> 本アプリは個人/少人数チーム向けのツールのため、本格的なユーザー管理システムではなく、**APIキー方式のシンプルな認証**を採用します。

---

## 変更内容

### バックエンド

#### [MODIFY] [app.py](file:///c:/Users/hikari/.gemini/新しいフォルダー/app.py)

1. **APIキー認証の追加**（脆弱性 #1 対応）
   - 環境変数 `API_KEY` でAPIキーを設定
   - データ変更系API（POST/DELETE）にAPIキー検証を追加
   - 閲覧・エクスポートは任意で保護可能（今回はデフォルト保護）

2. **CSRF対策の強化**（脆弱性 #2 対応）
   - `flask-wtf` は使わず、シンプルなカスタムトークン方式
   - ページ読み込み時にCSRFトークンを発行し、API呼び出し時に検証

3. **入力値の長さ制限**（脆弱性 #3 対応）
   - 各フィールド最大 5,000 文字
   - リクエストボディ最大サイズの設定

4. **レート制限の追加**（脆弱性 #4 対応）
   - `flask-limiter` によるAPI呼び出し回数制限
   - POST: 30回/分、GET: 60回/分、DELETE: 10回/分

5. **セキュリティヘッダーの設定**（脆弱性 #5 対応）
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `X-XSS-Protection: 1; mode=block`
   - `Content-Security-Policy`

6. **デバッグモードの明示的OFF**（脆弱性 #6 対応）

#### [MODIFY] [requirements.txt](file:///c:/Users/hikari/.gemini/新しいフォルダー/requirements.txt)

- `flask-limiter` を追加

---

### フロントエンド

#### [MODIFY] [index.html](file:///c:/Users/hikari/.gemini/新しいフォルダー/templates/index.html)

- CSRFトークンを `<meta>` タグで埋め込み
- APIキー入力用のログインUI（初回アクセス時にモーダルで入力、localStorageに保存）

#### [MODIFY] [app.js](file:///c:/Users/hikari/.gemini/新しいフォルダー/static/js/app.js)

- 全APIリクエストにAPIキーヘッダー（`X-API-Key`）を付与
- 全POST/DELETEリクエストにCSRFトークンを付与
- 認証エラー時にAPIキー入力を再要求

---

### デプロイ設定

#### [MODIFY] [render.yaml](file:///c:/Users/hikari/.gemini/新しいフォルダー/render.yaml)

- 環境変数 `API_KEY` と `SECRET_KEY` を追加（Renderのダッシュボードで設定）

## 検証計画

### ブラウザテスト
1. APIキーなしでアクセス → 認証モーダルが表示されること
2. 正しいAPIキーでログイン → 通常通り操作可能なこと
3. 不正なAPIキーでログイン → エラーが表示されること
4. 入力値に5,001文字以上 → 拒否されること
