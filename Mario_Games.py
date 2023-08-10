import requests
from bs4 import BeautifulSoup
import sqlite3
import re

# Function to sanitize table names
def sanitize_console_name(name):
    # Remove special characters, replace spaces with underscores, and replace consecutive underscores with a single underscore
    sanitized_name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    # Ensure the table name doesn't start or end with an underscore
    sanitized_name2 = sanitized_name.strip("_")
    return sanitized_name2

# Function to extract the year from the game title using regular expressions
def extract_year_from_title(year):
    pattern = r"\((\d{4})"  # Regular expression to match "(year" pattern
    match = re.search(pattern, year)
    if match:
        return match.group(1)  # Return the first four digits (the year)
    return None

# Function to clean the game title by removing unwanted text
def clean_game_title(game_title):
    # Remove right parenthesis and any remaining text after it
    title = re.sub(r"\s*\)\s*$|\s*\(\d{4}", "", game_title)
    # Remove any remaining text after the first parenthesis
    title2 = title.split(" (")[0]
    return title2.strip()

# Fetch the HTML content of the page
url = "https://nintendo.fandom.com/wiki/List_of_Mario_games"
response = requests.get(url)
html_content = response.text

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, "html.parser")

# Find the main content area where consoles and games are listed
content_area = soup.find("div", class_="mw-parser-output")

# Initialize a dictionary to store the console names and their respective games
console_games = {}

# Loop through each element in the content area
current_console = None
for element in content_area.children:
    # Check if the element is a console name (subheading)
    if element.name == "h2":
       current_console = element.text.strip()
       #Stops the script at "See also" part of the website.
       if current_console.startswith("See also"):
            break
       # Sanitize the console name to create a valid table name
       table_name = sanitize_console_name(current_console)
       console_games[table_name] = []
            
    elif element.name == "ul" and current_console:
        # If the element is an unordered list and we have a current console
        # Then, it contains the games for the current console
        games = element.find_all("li")
        #Creates an array of tuples
        games_list = []
        for game in games:
            game_name = game.text.strip()
            game_year = extract_year_from_title(game_name)
            game_title = clean_game_title(game_name)
            games_list.append((game_title, int(game_year)))
        console_games[table_name].extend(games_list)

# Connect to the SQLite database or create a new one if it doesn't exist
conn = sqlite3.connect("Mario_Game_Database.db")
cursor = conn.cursor()

# Loop through the consoles and create a table for each console with its games and years
for console, games_years in console_games.items():
    # Create a table for the console (if it doesn't exist)
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {console} (game TEXT, year INT)")
    # Insert games and years into the table
    for game_title, game_year in games_years:
        cursor.execute(f"INSERT INTO {console} (game, year) VALUES (?, ?)", (game_title, game_year))

# Commit changes and close the connection
conn.commit()
conn.close()
