from flask import Flask, jsonify, render_template
import mysql.connector
import pandas as pd

app = Flask(__name__)

db_config = {
    'user': 'root',
    'password': '',  # Default password (usually empty for Laragon)
    'host': 'localhost',
    'database': 'football_bi'  # Replace with your database name
}
csv_data = pd.read_csv('utils/fifa_data_updated.csv')


def calculate_outfield_attributes(player_row):
    PAC = round((player_row['Acceleration'] + player_row['SprintSpeed']) / 2, 1)
    SHO = round((player_row['Finishing'] + player_row['Volleys'] + player_row['ShotPower'] +
                 player_row['LongShots'] + player_row['Positioning'] + player_row['Penalties']) / 6, 1)
    PAS = round((player_row['Crossing'] + player_row['ShortPassing'] + player_row['LongPassing'] +
                 player_row['Curve'] + player_row['FKAccuracy'] + player_row['Vision']) / 6, 1)
    DRI = round((player_row['Dribbling'] + player_row['Agility'] + player_row['Balance'] +
                 player_row['Reactions'] + player_row['BallControl']) / 5, 1)
    DEF = round((player_row['Interceptions'] + player_row['Marking'] +
                 player_row['StandingTackle'] + player_row['SlidingTackle']) / 4, 1)
    PHY = round((player_row['Jumping'] + player_row['Stamina'] + player_row['Strength'] + 
                 player_row['Aggression']) / 4, 1)
    
    return {
        'PAC': PAC,
        'SHO': SHO,
        'PAS': PAS,
        'DRI': DRI,
        'DEF': DEF,
        'PHY': PHY
}

def calculate_gk_attributes(player_row):
    GKDiving = round(player_row['GKDiving'], 1)
    GKHandling = round(player_row['GKHandling'], 1)
    GKKicking = round(player_row['GKKicking'], 1)
    GKPositioning = round(player_row['GKPositioning'], 1)
    GKReflexes = round(player_row['GKReflexes'], 1)
    Reactions = round(player_row['Reactions'], 1)

    return {
        'GKDiving': GKDiving,
        'GKHandling': GKHandling,
        'GKKicking': GKKicking,
        'GKPositioning': GKPositioning,
        'GKReflexes': GKReflexes,
        'Reactions': Reactions
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
    
@app.route('/api/players/random', methods=['GET'])
def get_random_players():
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Query to fetch 10 random players from the database
        query = "SELECT * FROM player ORDER BY RAND() LIMIT 10"
        cursor.execute(query)
        players = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Check if any players were found
        if players:
            return jsonify(players)
        else:
            return jsonify({'error': 'No players found'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    

@app.route('/api/player/<name>', methods=['GET'])
def get_player_by_name(name):
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Query to fetch player data using partial matching
        query = "SELECT * FROM player WHERE Name LIKE %s"
        like_pattern = f"%{name}%"  # This will match any name containing the input string
        cursor.execute(query, (like_pattern,))
        players = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Check if any player data was found
        if players:
            return jsonify(players)
        else:
            return jsonify({'error': 'Player not found'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/player/<int:sofifa_id>')
def player(sofifa_id):
    try:
        # Find the corresponding player in the CSV using Sofifa_ID
        csv_player_data = csv_data[csv_data['Sofifa_ID'] == sofifa_id]

        # Check if player data is found in the CSV
        if csv_player_data.empty:
            return jsonify({'error': 'Player data not found in CSV'}), 404

        # Extract player data as a dictionary
        player_dict = csv_player_data.iloc[0].to_dict()

        # Determine the player's position(s)
        positions = player_dict['Position'].split(', ')
        
        # Check if the player is a goalkeeper (GK)
        if 'GK' in positions:
            radar_data = calculate_gk_attributes(csv_player_data.iloc[0])
        else:
            radar_data = calculate_outfield_attributes(csv_player_data.iloc[0])

        # Include the player's radar chart data and original CSV data in the response
        player_info = {
            'RadarData': radar_data,
            'CSVData': player_dict
        }

        # Return the data as JSON
        return jsonify(player_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/scout/player/<int:sofifa_id>')
def scouting_decision():
    pass


if __name__ == '__main__':
    app.run(debug=True)
