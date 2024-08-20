import pandas as pd
import mysql.connector
from mysql.connector import errorcode

# Define the path to the CSV file
csv_file_path = 'fifa_data_updated.csv'

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(csv_file_path)

# Select only the necessary columns
df = df[['Sofifa_ID', 'Name', 'Age', 'Photo', 'Nationality', 'Flag', 'Overall', 'Potential', 'Club', 'Club Logo', 'Position']]

# Replace NaN values with None (to be inserted as NULL in MySQL)
df = df.where(pd.notnull(df), None)

# Database connection details
db_config = {
    'user': 'root',  # Default username for MySQL
    'password': '',  # Default password (usually empty for local setups)
    'host': 'localhost',
    'database': 'football_bi'  # Replace with your database name
}

# Connect to the MySQL database
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Define the table name
    table_name = 'player'

    # Drop the table if it exists (optional, if you want to start fresh)
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Create the table with the specified columns
    create_table_query = f"""
    CREATE TABLE {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        Sofifa_ID INT NOT NULL UNIQUE,
        Name VARCHAR(255) NULL,
        Age INT NULL,
        Photo VARCHAR(255) NULL,
        Nationality VARCHAR(255) NULL,
        Flag VARCHAR(255) NULL,
        Overall INT NULL,
        Potential INT NULL,
        Club VARCHAR(255) NULL,
        Club_Logo VARCHAR(255) NULL,
        Position VARCHAR(255) NULL
    );
    """
    cursor.execute(create_table_query)

    # Insert data into the table
    insert_query = f"INSERT INTO {table_name} (Sofifa_ID, Name, Age, Photo, Nationality, Flag, Overall, Potential, Club, Club_Logo, Position) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    for index, row in df.iterrows():
        cursor.execute(insert_query, tuple(row))

    # Commit the transaction
    conn.commit()

    print(f"Data successfully imported into the '{table_name}' table.")

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
