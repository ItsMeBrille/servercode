from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime

DATABASE = 'data/beer_logs.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS beer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                bar_name TEXT NOT NULL,
                team_name TEXT NOT NULL,
                beer_type TEXT NOT NULL
            )
        ''')

def log_beer(bar_name: str, team_name: str, beer_type: str):
    valid_types = ["CISK", "KS", "LKSK", "SKSK"]
    if team_name not in valid_types:
        raise ValueError(f"Invalid beer type: {team_name}. Must be one of {valid_types}")

    timestamp = datetime.now().isoformat()
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''INSERT INTO beer_logs (timestamp, bar_name, team_name, beer_type) VALUES (?, ?, ?, ?) ''', (timestamp, bar_name, team_name, beer_type))

def get_team_count(team_name: str):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute('''
            SELECT COUNT(*) FROM beer_logs WHERE team_name = ?
        ''', (team_name,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
def get_all_count(team_name: str):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute('''SELECT beer_type, COUNT(*) FROM beer_logs WHERE team_name = ? GROUP BY beer_type''', (team_name,))
        results = dict(cursor.fetchall())
        normal_count = results.get('normal', 0)
        mega_count = results.get('mega', 0)
        return (normal_count, mega_count)


init_db()


app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/button/<bar_name>", methods=["GET"])
def button_handler(bar_name):
    button = request.args.get("button")
    press_type = request.args.get("type")
    if button and button.isdigit():
        idx = int(button)
        if 0 <= idx <= 3:
            team = ["CISK", "KS", "LKSK", "SKSK"][idx]
            log_beer(bar_name, team, press_type)
            
            socketio.emit('press_one', {'bar_name': bar_name, 'team': team, 'press_type': press_type})

            count = get_team_count(team)
            return f"{team} er på sin {count} øl !!!!!!!", 200
    return "Button press recorded", 200


@socketio.on('connect')
def handle_connect():
    beer_counts = {bt: get_all_count(bt) for bt in ["CISK", "KS", "LKSK", "SKSK"]}
    if socketio:
        socketio.emit('update_all', beer_counts)

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, debug=True)
