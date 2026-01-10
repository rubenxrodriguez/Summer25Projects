import json
import pandas as pd
import os

folder_path = 'json/'

for filename in os.listdir(folder_path):
    if filename.endswith('.txt'):
        conf = filename.split('-')[0]
        with open(os.path.join(folder_path, filename), 'r') as file:
            data = json.load(file)
        df = pd.DataFrame(data)
        
        result = df[['fullName','teamMarket','playerId','height','mins','gp','drtgPlayer','ortgPlayer','ws','ows','dws','rapm',
                     'orapm','drapm','stl','blk','stlPg','blkPg']]
        
        result['mpg'] = result['mins'] / result['gp']
        result = result[['fullName','teamMarket','playerId','height','mpg','gp','drtgPlayer','ortgPlayer','ws','ows','dws','rapm',
                     'orapm','drapm','stl','blk','stlPg','blkPg']] 
        numeric_cols = result.select_dtypes(include=['float64', 'int64']).columns
        result[numeric_cols] = result[numeric_cols].round(2)
        print(f"{conf}::", result.head(3))
        result.to_csv(f'cbba/{conf}_players.csv', index=False)
