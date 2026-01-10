import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import numpy as np

# Load FIBA data
fiba_df = pd.read_csv("csv_files/synergy_brazil.csv")

# Load team names from composite rankings
team_df = pd.read_csv("5year_stats/composite_srs_rankings2.csv")
team_names = team_df['team'].unique()

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
def extract_season_team_and_stats(best_season_str, team_names):
    # Split the string into parts
    parts = best_season_str.split()
    
    # First part is always the season
    season = parts[0]
    remaining_str = ' '.join(parts[1:])
    
    # Sort team names by length (longest first) to handle multi-word names
    sorted_teams = sorted(team_names, key=lambda x: -len(x.split()))
    
    for team in sorted_teams:
        if remaining_str.startswith(team):
            # Found the team name - what follows is the stats
            stats_str = remaining_str[len(team):].strip()
            return season, team, stats_str.split()
    
    # Fallback if no team found (shouldn't happen if team_names is complete)
    return season, None, parts[1:]

for _, player in fiba_df.iterrows():
    try:
        # Format search URL (Sports-Reference uses hyphenated names)
        search_name = player['NAME'].lower().replace(" ", "-")
        search_url = f"https://www.sports-reference.com/cbb/players/{search_name}-1.html"
        
        driver.get(search_url)
        time.sleep(2)  # Be polite with delays
        
        # Check if page exists
        if "Page Not Found" in driver.title:
            print(f"No page found for {player['NAME']}")
            continue
            
        # Extract all rows of stats
        table = wait.until(EC.presence_of_element_located((By.ID, "players_per_game")))
        rows = table.text.split("\n")
        


        # Parse table
        headers = rows[0].split()
        career_data = {}
        
        
        for row in rows[1:]:
            cols = row.split()
            if len(cols)>1 and cols[1].isnumeric():
                stats = cols
                headers_trimmed = [headers[0]] + headers[5:]
                career_stats = dict(zip(headers_trimmed,stats))
                career_data = {
                    'Player': player['NAME'],
                    'PTS/G_career': float(career_stats['PTS']),
                    'STL_BLK_career': float(career_stats['STL']) + float(career_stats['BLK']),
                    'G_career': int(career_stats['G'])
                }
                
                # Calculate PER
                career_data['PER_career'] = calculate_per({
                    'PTS': float(career_stats['PTS'])*int(career_stats['G']),
                    'AST': float(career_stats['AST'])*int(career_stats['G']),
                    'TRB': float(career_stats['TRB'])*int(career_stats['G']),
                    'STL': float(career_stats['STL'])*int(career_stats['G']),
                    'BLK': float(career_stats['BLK'])*int(career_stats['G']),
                    'TOV': float(career_stats['TOV'])*int(career_stats['G']),
                    'FG': float(career_stats['FG'])*int(career_stats['G']),
                    'FGA': float(career_stats['FGA'])*int(career_stats['G']),
                    'FT': float(career_stats['FT'])*int(career_stats['G']),
                    'FTA': float(career_stats['FTA'])*int(career_stats['G']),
                    'G': int(career_stats['G'])
                })
                break
                
        # Find best season stats
        best_season = max(rows[1:-1], key=lambda x: float(x.split()[-1]))
        season, team, stats = extract_season_team_and_stats(best_season, team_names)

        if team:
            # the stats now contain everything after season and team
            # headers after season and team are : ['conf','year','pos','g','gs','mp'...]
            best_stats = dict(zip(headers[2:],stats)) # skip season and team columns

            career_data.update({
                'best_season': season, # add season year
                'PTS/G_best': float(best_stats['PTS']),
                'STL_BLK_best': float(best_stats['STL']) + float(best_stats['BLK']),
                'PER_best': calculate_per({
                    'PTS': float(best_stats['PTS'])*int(best_stats['G']),
                    'AST': float(best_stats['AST'])*int(best_stats['G']),
                    'TRB': float(best_stats['TRB'])*int(best_stats['G']),
                    'STL': float(best_stats['STL'])*int(best_stats['G']),
                    'BLK': float(best_stats['BLK'])*int(best_stats['G']),
                    'TOV': float(best_stats['TOV'])*int(best_stats['G']),
                    'FG': float(best_stats['FG'])*int(best_stats['G']),
                    'FGA': float(best_stats['FGA'])*int(best_stats['G']),
                    'FT': float(best_stats['FT'])*int(best_stats['G']),
                    'FTA': float(best_stats['FTA'])*int(best_stats['G']),
                    'G': int(best_stats['G'])
                })
            })
            # Round all numeric values in career_data
            for key, value in career_data.items():
                if isinstance(value, float):
                    career_data[key] = round(value, 2)
                elif isinstance(value, int):
                    career_data[key] = int(round(value))
            ncaa_stats.append(career_data)
            print(f"Scraped {player['NAME']} successfully")
        
    except Exception as e:
        print(f"Error processing {player['NAME']}: {str(e)}")
        continue

driver.quit()

# Merge with FIBA data
final_df = pd.merge(
    fiba_df, 
    pd.DataFrame(ncaa_stats),
    left_on='NAME',
    right_on='Player',
    how='left'
).drop('Player', axis=1)

# Drop rows where PER_career is NaN or empty
final_df = final_df.dropna(subset=['PER_career'])
# Save results
final_df.to_csv('fiba_ncaa_brazil.csv', index=False)
print("Scraping complete! Saved to fiba_ncaa_merged.csv")
