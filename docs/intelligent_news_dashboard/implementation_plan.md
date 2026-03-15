# インテリジェント・ビジュアル・ニュース・ダッシュボード 実装計画

## 目標
Next.js と Tailwind CSS を使用して「インテリジェント・ビジュアル・ニュース・ダッシュボード」を開発します。
主な機能：
- ニューステーマの検索バー。
- ニュース取得のためのモックデータ連携。
- AIコンテンツ生成（要約と画像のモック）。
- レスポンシブでサイバーパンク風のUI。

## 変更内容

### プロジェクト構造
- `intelligent-news-dashboard/` (プロジェクトルート)
    - `app/` (Next.js App Router)
        - `page.tsx`: メインダッシュボード
        - `api/news/route.ts`: モックニュースAPI
        - `layout.tsx`: グローバルレイアウト
    - `components/`
        - `NewsCard.tsx`: 個別のニュース項目表示
        - `SearchBar.tsx`: 検索入力
        - `Dashboard.tsx`: グリッドコンテナ
    - `lib/`
        - `mockData.ts`: モックデータ生成
        - `utils.ts`: ヘルパー関数

### 依存関係
- `lucide-react`: アイコン用
- `framer-motion`: アニメーション用
- `clsx`, `tailwind-merge`: クラス管理用

## 検証計画
### 自動テスト
- `npm run dev` を実行し、localhost:3000 で動作確認。
### 手動検証
1. 検索バーにキーワードを入力 -> モック結果が表示されるか確認。
2. モバイルビューでのレスポンシブ動作確認。
3. ホバーエフェクトとアニメーションの確認。
