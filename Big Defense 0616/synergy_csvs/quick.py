import json
import pandas as pd
import os

folder_path = 'synergy_csvs/'

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        conf = filename.split('-')[0]
        df = pd.read_csv(os.path.join(folder_path, filename))
        df['conf'] = conf.upper()
        df.to_csv(os.path.join(folder_path, filename), index=False)
        print(f"Processed {filename}")