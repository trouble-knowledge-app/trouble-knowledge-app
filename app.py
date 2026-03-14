"""
トラブル＆ナレッジ記録Webアプリ
機械設計エンジニア向け
"""

import os
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge.db")


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


@app.route("/")
def index():
    """メインページを表示"""
    return render_template("index.html")


@app.route("/api/records", methods=["GET"])
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
def create_record():
    """新規記録を保存"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "データが送信されていません"}), 400

    required = ["phenomenon", "cause", "response", "future_note"]
    for field in required:
        if not data.get(field, "").strip():
            return jsonify({"error": f"{field} は必須です"}), 400

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
def delete_record(record_id):
    """記録を削除"""
    conn = get_db()
    conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "削除しました"}), 200


# アプリ起動時にDB初期化（gunicorn対応）
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
