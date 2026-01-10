import json
import pandas as pd
import os

folder_path = 'cbba/'

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        conf = filename.split('_')[0]
        df = pd.read_csv(os.path.join(folder_path, filename))
        df['conf'] = conf.upper()
        df.to_csv(os.path.join(folder_path, filename), index=False)
        print(f"Processed {filename}")