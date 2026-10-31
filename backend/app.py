from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "mysql-service")
DB_NAME = os.environ.get("DB_NAME", "appdb")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "apppassword")


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/api")
def api():
    return jsonify({
        "message": "Hello from the backend!",
        "database": DB_HOST
    })


@app.route("/api/users", methods=["GET"])
def get_users():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email FROM users")

    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(users)


@app.route("/api/users", methods=["POST"])
def create_user():

    data = request.get_json()

    name = data["name"]
    email = data["email"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        (name, email)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "message": "User created successfully"
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
