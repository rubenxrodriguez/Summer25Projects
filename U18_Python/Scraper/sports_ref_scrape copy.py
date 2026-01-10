import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import numpy as np

# Load FIBA data
fiba_df = pd.read_csv("csv_files/synergy_australia.csv")

# Initialize browser
driver = webdriver.Chrome()
driver.get("https://www.sports-reference.com/cbb/")
wait = WebDriverWait(driver, 10)


# Storage for results
ncaa_stats = []

def calculate_per(row):
    """Calculate Player Efficiency Rating (simplified)"""
    return ((row['PTS'] + row['AST'] + row['TRB'] + row['STL'] + row['BLK'] - 
             row['TOV'] - (row['FGA'] - row['FG']) - (row['FTA'] - row['FT'])) / 
            row['G'])

def parse_stats_table(table_text):
    """Properly parse the stats table accounting for multi-word columns"""
    lines = table_text.split('\n')
    headers = ['Season', 'Team', 'Conf', 'Class', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', 
               '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 
               'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'Awards']
    
    seasons = []
    current_line = []
    
    # Handle multi-line season entries (where awards wrap)
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) > 5 and parts[0][0].isdigit():  # New season
            if current_line:
                seasons.append(' '.join(current_line))
            current_line = [line]
        else:
            current_line.append(line)
    
    if current_line:
        seasons.append(' '.join(current_line))
    
    # Parse each season
    season_data = []
    for season in seasons:
        parts = season.split()
        season_dict = {}
        i = 0
        for header in headers:
            if header == 'Awards' and i < len(parts):
                season_dict[header] = ' '.join(parts[i:])
                break
            if i < len(parts):
                season_dict[header] = parts[i]
                i += 1
            else:
                season_dict[header] = None
        season_data.append(season_dict)
    
    return season_data

def get_best_season(season_data):
    """Identify best season by game-weighted PER"""
    best = None
    best_per = -float('inf')
    
    for season in season_data:
        try:
            # Convert stats to numeric values
            stats = {
                'PTS': float(season['PTS']),
                'AST': float(season['AST']),
                'TRB': float(season['TRB']),
                'STL': float(season['STL']),
                'BLK': float(season['BLK']),
                'TOV': float(season['TOV']),
                'FG': float(season['FG']),
                'FGA': float(season['FGA']),
                'FT': float(season['FT']),
                'FTA': float(season['FTA']),
                'G': int(season['G'])
            }
            
            per = calculate_per(stats)
            weighted_per = per * stats['G']  # Weight by games played
            
            if weighted_per > best_per:
                best_per = weighted_per
                best = season
        except (ValueError, TypeError):
            continue
            
    return best

for _, player in fiba_df.iterrows():
    try:
        driver.get(f"https://www.sports-reference.com/cbb/players/{player['NAME'].lower().replace(' ', '-')}-1.html")
        time.sleep(2)
        
        if "Page Not Found" in driver.title:
            continue
            
        table = wait.until(EC.presence_of_element_located((By.ID, "players_per_game")))
        season_data = parse_stats_table(table.text)
        
        if not season_data:
            continue
            
        # Get career stats (last row)
        career_stats = season_data[-1] if 'Career' in season_data[-1]['Season'] else None
        
        # Find best season
        best_season = get_best_season(season_data[:-1])  # Exclude career row
        
        if career_stats and best_season:
            ncaa_stats.append({
                'Player': player['NAME'],
                'PTS/G_career': float(career_stats['PTS']),
                'STL_BLK_career': float(career_stats['STL']) + float(career_stats['BLK']),
                'PER_career': calculate_per({
                    'PTS': float(career_stats['PTS'])*int(career_stats['G']),
                    # ... other stats multiplied by G
                }),
                'PTS/G_best': float(best_season['PTS']),
                'STL_BLK_best': float(best_season['STL']) + float(best_season['BLK']),
                'PER_best': calculate_per({
                    'PTS': float(best_season['PTS'])*int(best_season['G']),
                    # ... other stats multiplied by G
                }),
                'Best_Season_Year': best_season['Season']
            })
    except Exception as e:
        print(f"Error with {player['NAME']}: {str(e)}")