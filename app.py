from flask import Flask, jsonify, render_template, request
import mysql.connector
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier, export_text
import numpy as np
import requests


app = Flask(__name__)

db_config = {
    'user': 'root',
    'password': '',  
    'host': 'localhost',
    'database': 'football_bi' 
}

csv_data = pd.read_csv('utils/fifa_data_updated.csv')
df = pd.read_csv('utils/fifa_data_updated.csv')

position_features = {
    'GK': ['GKDiving', 'GKHandling', 'GKKicking', 'GKPositioning', 'GKReflexes'],
    'LW': ['Crossing', 'Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'FKAccuracy', 'LongPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'RW': ['Crossing', 'Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'FKAccuracy', 'LongPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'ST': ['Finishing', 'HeadingAccuracy', 'ShortPassing', 'Volleys', 'Dribbling', 'Curve', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CAM': ['ShortPassing', 'Dribbling', 'Finishing', 'BallControl', 'Vision', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CM': ['ShortPassing', 'Dribbling', 'BallControl', 'Vision', 'Acceleration', 'SprintSpeed', 'Agility'],
    'CDM': ['StandingTackle', 'Strength', 'ShortPassing', 'BallControl', 'Acceleration', 'SprintSpeed', 'Agility'],
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

        cursor.execute(count_query, params[:-2])
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

        # return jsonify(player_info)
        return render_template('player.html', player=player_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scout', methods=['GET', 'POST'])
def scouting():
    positions = request.args.get('positions')
    club = request.args.get('club', '')

    players = []

    if request.method == 'POST':
        positions = request.form.get('positions')
        club = request.form.get('club', '').strip()

        if positions and club:
            response = requests.get('http://127.0.0.1:5000/api/scouting', params={'positions': positions, 'club': club})
            if response.status_code == 200:
                data = response.json()
                players = data.get('players', [])

    return render_template('scouting.html', players=players, positions=positions, club=club)


@app.route('/api/scouting', methods=['GET'])
def find_fit_players():
    position = request.args.get('positions')
    club = request.args.get('club', '').strip()

    if not position or not club:
        return jsonify({'error': 'Both position and club are required'}), 400

    position_features_list = position_features.get(position, [])
    if len(position_features_list) < 1:
        return jsonify({'error': 'Not enough features to train the model for this position'}), 400

    players = df[df['Position'] == position]

    if players.empty:
        return jsonify({'error': f'No players found for position {position}'}), 404

    players = players.copy()
    in_club = players[players['Club'].str.lower() == club.lower()]
    outside_club = players[players['Club'].str.lower() != club.lower()]

    if not in_club.empty:
        outside_club_sample = outside_club.sample(n=len(in_club), random_state=42)
        balanced_players = pd.concat([in_club, outside_club_sample])
    else:
        return jsonify({'error': f'No players found for club {club}'}), 404

    balanced_players = balanced_players.sample(frac=1, random_state=42).reset_index(drop=True)
    balanced_players['FitForClub'] = balanced_players['Club'].apply(
        lambda x: 1 if isinstance(x, str) and x.lower() == club.lower() else 0
    )

    X = balanced_players[position_features_list].select_dtypes(include=['float64', 'int64'])
    y = balanced_players['FitForClub']

    model = DecisionTreeClassifier(criterion='entropy', min_samples_split=3)
    model.fit(X, y)

    X_all = df[df['Position'] == position][position_features_list].select_dtypes(include=['float64', 'int64'])
    X_all = X_all[position_features_list]
    
    df_copy = df.copy()
    df_copy.loc[df_copy['Position'] == position, 'FitPrediction'] = model.predict(X_all)

    fit_players = df_copy[(df_copy['FitPrediction'] == 1) & (df_copy['Position'] == position)]

    if fit_players.empty:
        return jsonify({'message': 'No players found that fit the criteria'}), 200

    def explain_fit(player_row):
        feature_values = player_row[position_features_list].to_dict()
        explanation = []

        for node_id in range(model.tree_.node_count):
            if model.tree_.feature[node_id] != -2:  # Not a leaf node
                feature_name = position_features_list[model.tree_.feature[node_id]]
                threshold = model.tree_.threshold[node_id]
                feature_value = feature_values[feature_name]
                
                comparison = '>' if feature_value > threshold else '<='
                
                explanation.append({
                    'Feature': feature_name,
                    'Value': f"{feature_value:.2f}",
                    'Threshold': f"{threshold:.2f}",
                    'Comparison': comparison
                })

        class_label = model.apply([player_row[position_features_list].values])[0]
        final_classification = 'fit' if bool(model.tree_.value[class_label][0].argmax() == 1) else 'not fit'
        
        return {
            'Features': explanation,
            'Classification': final_classification
        }

    fit_players_info = []
    for _, row in fit_players.iterrows():
        player_info = {
            'Sofifa_ID': row['Sofifa_ID'],
            'Name': row['Name'],
            'Age': row['Age'],
            'Club': row['Club'],
            'Photo': row['Photo'],  # Add photo URL
            'Position': row['Position'],
            'Explanation': explain_fit(row)
        }
        fit_players_info.append(player_info)

    # Get the first feature for sorting
    first_feature = position_features_list[0]

    # Sort players by the value of the first feature in the explanation
    top_fit_players = sorted(
        fit_players_info,
        key=lambda x: float(next(
            (f['Value'] for f in x['Explanation']['Features'] if f['Feature'] == first_feature),
            0  # Default value if the feature is not found
        )),
        reverse=True  # Sort in descending order for the highest value first
    )[:50]

    return jsonify({'players': top_fit_players})


if __name__ == '__main__':
    app.run(debug=True)
