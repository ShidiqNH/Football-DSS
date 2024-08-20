import pandas as pd

# Define the path to the CSV file
csv_file_path = 'fifa_data.csv'

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(csv_file_path)

# Function to format the Sofifa_ID
def format_sofifa_id(sofifa_id):
    # Convert the ID to a string and pad with leading zeros if necessary
    sofifa_id_str = str(sofifa_id).zfill(6)  # Ensures the ID is at least 6 digits long
    # Split the ID into two parts: the first 3 digits and the last 3 digits
    part1 = sofifa_id_str[:3]
    part2 = sofifa_id_str[3:]
    return f"{part1}/{part2}"

# Update the 'Photo' column with the new URLs
df['Photo'] = df['Sofifa_ID'].apply(lambda x: f"https://cdn.sofifa.net/players/{format_sofifa_id(x)}/24_120.png")

# Print or save the DataFrame with the updated 'Photo' column
print(df[['Sofifa_ID', 'Photo']])

# Optionally, save the updated DataFrame to a new CSV file
df.to_csv('fifa_data_updated.csv', index=False)

