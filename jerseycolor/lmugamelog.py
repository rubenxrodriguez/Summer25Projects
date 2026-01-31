import pandas as pd 
import certifi
import ssl
from urllib.request import urlopen
from io import StringIO

GAMELOG_URL = "https://raw.githubusercontent.com/rubenxrodriguez/WCC_ESPN_Scraper/main/WCC_Fantasy_1231/Gamelog/gamelog.csv"

ctx = ssl.create_default_context(cafile=certifi.where())

with urlopen(GAMELOG_URL, context=ctx) as r:
    csv_text = r.read().decode("utf-8")

gamelogs = pd.read_csv(StringIO(csv_text))


LMU = "Loyola Marymount Lions"
df = gamelogs[(gamelogs['Team'] == LMU) | (gamelogs['Opponent'] == LMU)]
df.to_csv('lmugamelog0127.csv',index=False)