# ナレッジエクスポート機能の追加

保存したナレッジ（記録）を指定したファイル形式でダウンロードできる機能を追加する。

## 対応フォーマット

| 形式 | 説明 |
|------|------|
| CSV | Excel等で開ける表形式 |
| JSON | プログラムで再利用しやすい形式 |
| テキスト | 人間が読みやすいプレーンテキスト形式 |

## 変更内容

---

### バックエンド

#### [MODIFY] [app.py](file:///c:/Users/hikari/.gemini/新しいフォルダー/app.py)

- `GET /api/records/export?format=csv|json|txt` エンドポイントを追加
- `csv`, `json`, `txt` の3形式に対応
- 検索フィルタ `q` パラメータにも対応（現在表示中の記録のみエクスポート可能）
- `Content-Disposition` ヘッダーでファイル名を設定し、ブラウザにダウンロードさせる
- `import csv, io, json` を追加

---

### フロントエンド

#### [MODIFY] [index.html](file:///c:/Users/hikari/.gemini/新しいフォルダー/templates/index.html)

- 検索バーの右側にエクスポートボタンを追加
- フォーマット選択用のドロップダウンメニューを追加（CSV / JSON / テキスト）

#### [MODIFY] [app.js](file:///c:/Users/hikari/.gemini/新しいフォルダー/static/js/app.js)

- エクスポートボタンのクリックでドロップダウンを表示/非表示
- 各フォーマットをクリックすると `/api/records/export?format=xxx` にリクエストしてダウンロード
- 検索中の場合は `q` パラメータも付与

#### [MODIFY] [style.css](file:///c:/Users/hikari/.gemini/新しいフォルダー/static/css/style.css)

- エクスポートボタンとドロップダウンメニューのスタイルを追加
- 既存のデザインに統一した glassmorphism スタイル

## 検証計画

### ブラウザテスト
1. `python app.py` でローカルサーバーを起動
2. ブラウザで `http://localhost:5000` を開く
3. エクスポートボタンが表示されることを確認
4. CSV / JSON / テキスト の各形式でダウンロードできることを確認
5. 検索フィルタ中にエクスポートした場合、フィルタ結果のみ出力されることを確認
