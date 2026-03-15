"""
トラブル＆ナレッジ記録Webアプリ
機械設計エンジニア向け
"""

import os
import csv
import io
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, Response, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# --- セキュリティ設定 ---
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # リクエスト最大1MB

# APIキー（環境変数から取得、未設定時はデフォルト値）
API_KEY = os.environ.get("API_KEY", "change-me-in-production")

# フィールド最大文字数
MAX_FIELD_LENGTH = 5000

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge.db")

# レート制限
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)


def get_db():
    """データベース接続を取得"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """データベースの初期化"""
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phenomenon TEXT NOT NULL,
            cause TEXT NOT NULL,
            response TEXT NOT NULL,
            future_note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


# --- セキュリティヘッダー ---
@app.after_request
def set_security_headers(response):
    """全レスポンスにセキュリティヘッダーを付与"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
    )
    return response


# --- APIキー認証デコレータ ---
def require_api_key(f):
    """APIキー認証を要求するデコレータ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if not key or key != API_KEY:
            return jsonify({"error": "認証に失敗しました。APIキーが正しくありません。"}), 401
        return f(*args, **kwargs)
    return decorated


# --- CSRFトークン ---
def generate_csrf_token():
    """CSRFトークンを生成してセッションに保存"""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf_token():
    """リクエストのCSRFトークンを検証"""
    token = request.headers.get("X-CSRF-Token", "")
    if not token or token != session.get("_csrf_token"):
        return False
    return True


# Jinja2テンプレートでCSRFトークンを使用可能にする
app.jinja_env.globals["csrf_token"] = generate_csrf_token


# --- ルート ---
@app.route("/")
def index():
    """メインページを表示"""
    return render_template("index.html")


@app.route("/api/auth/verify", methods=["POST"])
@limiter.limit("10 per minute")
def verify_api_key():
    """APIキーの検証"""
    data = request.get_json()
    if not data or not data.get("api_key"):
        return jsonify({"error": "APIキーが必要です"}), 400
    if data["api_key"] != API_KEY:
        return jsonify({"error": "APIキーが正しくありません"}), 401
    return jsonify({"message": "認証成功", "csrf_token": generate_csrf_token()}), 200


@app.route("/api/records", methods=["GET"])
@require_api_key
@limiter.limit("60 per minute")
def get_records():
    """記録を取得（検索クエリ対応）"""
    query = request.args.get("q", "").strip()
    conn = get_db()

    if query:
        search = f"%{query}%"
        rows = conn.execute(
            """
            SELECT * FROM records
            WHERE phenomenon LIKE ?
               OR cause LIKE ?
               OR response LIKE ?
               OR future_note LIKE ?
            ORDER BY created_at DESC
            """,
            (search, search, search, search),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM records ORDER BY created_at DESC"
        ).fetchall()

    conn.close()

    records = []
    for row in rows:
        records.append(
            {
                "id": row["id"],
                "phenomenon": row["phenomenon"],
                "cause": row["cause"],
                "response": row["response"],
                "future_note": row["future_note"],
                "created_at": row["created_at"],
            }
        )

    return jsonify(records)


@app.route("/api/records", methods=["POST"])
@require_api_key
@limiter.limit("30 per minute")
def create_record():
    """新規記録を保存"""
    # CSRF検証
    if not validate_csrf_token():
        return jsonify({"error": "不正なリクエストです（CSRF検証失敗）"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "データが送信されていません"}), 400

    required = ["phenomenon", "cause", "response", "future_note"]
    for field in required:
        value = data.get(field, "")
        if not isinstance(value, str):
            return jsonify({"error": f"{field} は文字列である必要があります"}), 400
        if not value.strip():
            return jsonify({"error": f"{field} は必須です"}), 400
        if len(value) > MAX_FIELD_LENGTH:
            return jsonify({"error": f"{field} は{MAX_FIELD_LENGTH}文字以内にしてください"}), 400

    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO records (phenomenon, cause, response, future_note)
        VALUES (?, ?, ?, ?)
        """,
        (
            data["phenomenon"].strip(),
            data["cause"].strip(),
            data["response"].strip(),
            data["future_note"].strip(),
        ),
    )
    conn.commit()

    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM records WHERE id = ?", (new_id,)).fetchone()
    conn.close()

    return jsonify(
        {
            "id": row["id"],
            "phenomenon": row["phenomenon"],
            "cause": row["cause"],
            "response": row["response"],
            "future_note": row["future_note"],
            "created_at": row["created_at"],
        }
    ), 201


@app.route("/api/records/<int:record_id>", methods=["DELETE"])
@require_api_key
@limiter.limit("10 per minute")
def delete_record(record_id):
    """記録を削除"""
    # CSRF検証
    if not validate_csrf_token():
        return jsonify({"error": "不正なリクエストです（CSRF検証失敗）"}), 403

    conn = get_db()
    conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "削除しました"}), 200


@app.route("/api/records/export", methods=["GET"])
@require_api_key
@limiter.limit("20 per minute")
def export_records():
    """記録をファイルとしてエクスポート"""
    fmt = request.args.get("format", "csv").lower()
    if fmt not in ("csv", "json", "txt"):
        return jsonify({"error": "サポートされていない形式です"}), 400

    query = request.args.get("q", "").strip()
    conn = get_db()

    if query:
        search = f"%{query}%"
        rows = conn.execute(
            """
            SELECT * FROM records
            WHERE phenomenon LIKE ?
               OR cause LIKE ?
               OR response LIKE ?
               OR future_note LIKE ?
            ORDER BY created_at DESC
            """,
            (search, search, search, search),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM records ORDER BY created_at DESC"
        ).fetchall()

    conn.close()

    records = []
    for row in rows:
        records.append(
            {
                "id": row["id"],
                "phenomenon": row["phenomenon"],
                "cause": row["cause"],
                "response": row["response"],
                "future_note": row["future_note"],
                "created_at": row["created_at"],
            }
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"knowledge_{timestamp}"

    if fmt == "json":
        import json as json_mod
        content_str = json_mod.dumps(records, ensure_ascii=False, indent=2)
        data = content_str.encode("utf-8")
        filename = f"{filename_base}.json"
        return Response(
            data,
            mimetype="application/json",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Content-Type": "application/json; charset=utf-8",
            },
        )

    elif fmt == "txt":
        lines: list[str] = []
        for i, r in enumerate(records, 1):
            lines.append("=" * 52)
            lines.append(f"  記録 #{i}  |  {r['created_at']}")
            lines.append("=" * 52)
            lines.append(f"【事象】\n{r['phenomenon']}\n")
            lines.append(f"【原因の推測】\n{r['cause']}\n")
            lines.append(f"【現場の対応】\n{r['response']}\n")
            lines.append(f"【未来の自分への指示】\n{r['future_note']}\n")
        content_str = "\n".join(lines)
        data = content_str.encode("utf-8")
        filename = f"{filename_base}.txt"
        return Response(
            data,
            mimetype="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Content-Type": "text/plain; charset=utf-8",
            },
        )

    else:  # csv
        output = io.BytesIO()
        # BOM付きUTF-8 (Excel対応)
        output.write(b"\xef\xbb\xbf")
        wrapper = io.TextIOWrapper(output, encoding="utf-8", newline="")
        writer = csv.writer(wrapper)
        writer.writerow(["ID", "事象", "原因の推測", "現場の対応", "未来の自分への指示", "記録日時"])
        for r in records:
            writer.writerow([
                r["id"],
                r["phenomenon"],
                r["cause"],
                r["response"],
                r["future_note"],
                r["created_at"],
            ])
        wrapper.flush()
        data = output.getvalue()
        filename = f"{filename_base}.csv"
        return Response(
            data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )


# アプリ起動時にDB初期化（gunicorn対応）
init_db()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
