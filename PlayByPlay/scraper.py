import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

#stats_to_keep = [MIN,OREB,DREB,REB,AST,STL,BLK,TO,PF,FGM,FGA,3PM,3PA,FTM,FTA,PTS,]
# we want to keep these for each player and for the whole team 

link = "https://stats.ncaa.org/contests/6473998/play_by_play"
driver = webdriver.Chrome()
driver.get(link)
time.sleep(1)
rows = driver.find_elements(By.TAG_NAME, "tr")
time.sleep(1)
for row in rows[:100]:
    if "shot" in row.text.lower():
        print(row.text)

time.sleep(.2)

# row 01 : 1 2 3 4 s
# row 02 :portland 16 16 19 17 68
# row 03 : lmu (ca) 15 16 18 28 77
# row 04 : 01/22/2026 09:00 pm
# row 05 : albert gersten pav
headers = rows[9].text
# 'Time\nPortland\nScore\nLMU (CA)'
headers = headers.split("\n")

#example rows : 
#'01:11:00 Tiffany Barbosa, 2pt drivinglayup fromturnover;pointsinthepaint; missed 10-15'
#'01:11:00 10-15 Zawadi Ogot, foul personal shooting;2freethrow;'
# '00:00:00 period end confirmed;'