from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time
import numpy as np

countries_list = [
    "Australia",
    "Brazil",
    "Bulgaria",
    "Canada",
    "Croatia",
    "Czechia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Ireland",
    "Italy",
    "Netherlands",
    "New Zealand",
    "Nigeria",
    "Poland",
    "Romania",
    "Serbia",
    "Spain",
    "Sweden",
    "Switzerland",
    "UK"
]

# Configuration
URL_LIST = [
    ("https://apps.synergysports.com/basketball/teams/5787f8e3576202139848e0d0/boxscore?seasonId=62022000ef4e6d1f884be241&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true", "U18", "2022","Brazil"),

    ("https://apps.synergysports.com/basketball/teams/5787f8e3576202139848e0d0/boxscore?seasonId=60c6ff1ff172c7ea936560f4&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true", "U18", "2021","Brazil"),

    ("https://apps.synergysports.com/basketball/teams/54457df8300969b132fd107c/boxscore?seasonId=62a653296b7b4c5617e75bd1&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true", "U17", "2023","Brazil"),

    ("https://apps.synergysports.com/basketball/teams/5d067f8ff52909811e46bca7/boxscore?perGame=true&seasonId=62a653296b7b4c5617e75bd1&competitionKey=54457dce300969b132fcfb41:ALL", "U16", "2023","Brazil"),

    ("https://apps.synergysports.com/basketball/teams/5d067f8ff52909811e46bca7/boxscore?perGame=true&seasonId=60c6ff1ff172c7ea936560f4&competitionKey=54457dce300969b132fcfb41:ALL", "U16", "2021","Brazil")
]

def scrape_synergy_data():
    driver = webdriver.Chrome()
    
    try:
        # Login once
        driver.get("https://apps.synergysports.com/basketball/teams/5c972227f52909811e452c6f/boxscore?seasonId=5b1d58749559b26e7e35069b&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "Username")))
        
        driver.find_element(By.NAME, "Username").send_keys("rrodr102@lion.lmu.edu")
        driver.find_element(By.NAME, "Password").send_keys("Euclideanspace3#")
        driver.find_element(By.CSS_SELECTOR, ".btn").click()
        time.sleep(2)
        
        all_players = []
        
        for url, fiba_class, fiba_year,fiba_country in URL_LIST:
            driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Extract data
            rows = driver.find_elements(By.CLASS_NAME, "cdk-row.ts-row.ng-star-inserted")
            
            for row in rows:
                try:
                    lines = row.text.split("\n")
                    if len(lines) >= 3:
                        player_data = {
                            "NAME": ' '.join(lines[0].split()[1:]),
                            "GP": lines[1],
                            "ROLE": lines[2] if len(lines) > 3 else None,
                            "COUNTRY": fiba_country,
                            "FIBA_CLASS": fiba_class,
                            "FIBA_YEAR": fiba_year,
                            "SCRAPE_TIMESTAMP": pd.Timestamp.now()
                        }
                        
                        # Add stats if available
                        if len(lines) > 3:
                            stats = lines[-1].split()
                            stat_columns = ['POSS', 'PTS', 'PPP', 'AST', 'TO', 'FG%', '3FG_ATT', 
                                           '3FG%', 'EFG%', 'TOT_REB', 'FT_ATT', 'FT%', 'STL_BLK', 'AST_TO']
                            for col, val in zip(stat_columns, stats):
                                player_data[col] = val
                        
                        all_players.append(player_data)
                        
                except StaleElementReferenceException:
                    continue
            
        return pd.DataFrame(all_players)
    
    finally:
        driver.quit()

synergy_data = scrape_synergy_data()
print(synergy_data.head(3))
synergy_data.to_csv("csv_files/synergy_brazil.csv", index = False)