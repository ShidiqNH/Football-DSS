from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

db_config = {
    'user': 'root',
    'password': '',  # Default password (usually empty for Laragon)
    'host': 'localhost',
    'database': 'football_bi'  # Replace with your database name
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

@app.route('/api/get_all_players', methods=['GET'])
def get_all_players():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) 

        cursor.execute("SELECT * FROM player")
        players = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(players)

    except mysql.connector.Error as err:
        return str(err), 500
    


if __name__ == '__main__':
    app.run(debug=True)
