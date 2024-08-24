from flask import Flask, jsonify, render_template, request
import mysql.connector
import pandas as pd
import joblib

app = Flask(__name__)

db_config = {
    'user': 'root',
    'password': '',  # Default password (usually empty for Laragon)
    'host': 'localhost',
    'database': 'football_bi'  # Replace with your database name
}

csv_data = pd.read_csv('utils/fifa_data_updated.csv')
df = pd.read_csv('utils/fifa_data_updated.csv')

position_features = {
    'GK': ['GKDiving', 'GKHandling', 'GKKicking', 'GKPositioning', 'GKReflexes'],
    'LW': ['Crossing', 'Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'FKAccuracy', 'LongPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'RW': ['Crossing', 'Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'FKAccuracy', 'LongPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CF': ['Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'ST': ['Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'LF': ['Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'RF': ['Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CAM': ['ShortPassing', 'Dribbling', 'Finishing', 'BallControl', 'Vision', 'Acceleration', 'SprintSpeed', 'Agility'],
    'LM': ['Crossing', 'Dribbling', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CM': ['ShortPassing', 'Dribbling', 'BallControl', 'Vision', 'Acceleration', 'SprintSpeed', 'Agility'],
    'RM': ['Crossing', 'Dribbling', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CDM': ['StandingTackle', 'Strength', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'LWB': ['StandingTackle', 'Strength', 'Crossing', 'Dribbling', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'RWB': ['StandingTackle', 'Strength', 'Crossing', 'Dribbling', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'LB': ['StandingTackle', 'Strength', 'Crossing', 'Dribbling', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'RB': ['StandingTackle', 'Strength', 'Crossing', 'Dribbling', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CB': ['StandingTackle', 'Strength', 'HeadingAccuracy', 'Interceptions', 'Positioning', 'Jumping'],
}


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

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/players')
def players():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch the current page number from query parameters, default is 1
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        # Get filter values from query parameters
        position_filter = request.args.get('positions')
        club_filter = request.args.get('club')

        # Build the base query
        query = "SELECT Sofifa_ID, Photo, Name, Age, Overall, Club, Position FROM player"
        filters = []
        params = []

        # Add filters if present
        if position_filter:
            filters.append("Position = %s")
            params.append(position_filter)
        if club_filter:
            filters.append("Club LIKE %s")
            params.append(f"%{club_filter}%")

        # Add the WHERE clause if there are filters
        if filters:
            query += " WHERE " + " AND ".join(filters)

        # Add pagination
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        players = cursor.fetchall()

        # Get total players count with the same filters
        count_query = "SELECT COUNT(*) FROM player"
        if filters:
            count_query += " WHERE " + " AND ".join(filters)

        cursor.execute(count_query, params[:-2])  # Exclude pagination params for count query
        total_players = cursor.fetchone()['COUNT(*)']
        total_pages = (total_players + per_page - 1) // per_page

        cursor.close()
        conn.close()

        return render_template(
            "players.html", 
            players=players, 
            current_page=page, 
            total_pages=total_pages
        )

    except mysql.connector.Error as err:
        return str(err), 500

    
@app.route('/api/suggestions')
def suggestions():
    query = request.args.get('query', '')
    suggestion_type = request.args.get('type', '')

    if not query or not suggestion_type:
        return jsonify([])

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if suggestion_type == 'club':
            cursor.execute("SELECT DISTINCT Club FROM player WHERE Club LIKE %s ", (f"%{query}%",))
        else:
            return jsonify([])

        suggestions = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify(suggestions)

    except mysql.connector.Error as err:
        return jsonify([]), 500
    
@app.route('/api/player_suggestions')
def player_suggestions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = request.args.get('name', '')
        
        # Fetch players whose name contains the query
        cursor.execute("SELECT Sofifa_ID, Photo, Name FROM player WHERE Name LIKE %s LIMIT 10", (f'%{query}%',))
        players = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify(players)

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


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
    

@app.route('/api/player', methods=['GET'])
def get_players():
    # Get query parameters
    name = request.args.get('name')
    position = request.args.get('position')
    club = request.args.get('club')

    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Build the query based on provided parameters
        query = "SELECT * FROM player WHERE 1=1"
        params = []

        if name:
            query += " AND Name LIKE %s"
            params.append(f"%{name}%")

        if position:
            query += " AND Position = %s"
            params.append(position)

        if club:
            query += " AND Club = %s"
            params.append(club)

        # Check if there are no parameters provided
        if not params:
            return jsonify({'error': 'At least one parameter is required'}), 400

        cursor.execute(query, tuple(params))
        players = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Check if any player data was found
        if players:
            return jsonify(players)
        else:
            return jsonify({'error': 'No players found matching the criteria'}), 404

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

        return render_template('player_profile.html', player=player_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/scout/player/<int:sofifa_id>')
def scouting_decision(sofifa_id):
    # Find the player in the DataFrame
    player = df[df['Sofifa_ID'] == sofifa_id]
    
    if player.empty:
        return jsonify({'error': 'Player not found'}), 404
    
    # Get the player's position
    position = player.iloc[0]['Position']
    
    if position not in position_features:
        return jsonify({'error': f'Model for position {position} is not available'}), 400
    
    # Load the pre-trained model for the player's position
    model_filename = f'models/{position}_fit_model_balanced.pkl'
    try:
        model = joblib.load(model_filename)
    except FileNotFoundError:
        return jsonify({'error': f'Model for position {position} not found'}), 404
    
    # Prepare the player's data for prediction
    X_test = player[position_features[position]].select_dtypes(include=['float64', 'int64'])
    
    # Predict using the loaded model
    y_pred = model.predict(X_test)
    
    # Determine if the player is fit or not
    is_fit = bool(y_pred[0])
    
    return jsonify({
        'sofifa_id': sofifa_id,
        'name': player.iloc[0]['Name'],
        'position': position,
        'fit': is_fit,
    })



if __name__ == '__main__':
    app.run(debug=True)
