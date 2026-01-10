import os
import pandas as pd

folder_path = 'synergy_csvs/'
merged_df = pd.DataFrame()

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        df = pd.read_csv(os.path.join(folder_path, filename))
        merged_df = pd.concat([merged_df, df], ignore_index=True)

merged_df.to_csv('data/merged_synergy.csv', index=False)
print('merged synergy csvs')
# Merge cbba
cbba_path = 'cbba/'
merged_cbba = pd.DataFrame()

for filename in os.listdir(cbba_path):
    if filename.endswith('.csv'):
        df = pd.read_csv(os.path.join(cbba_path, filename))
        merged_cbba = pd.concat([merged_cbba, df], ignore_index=True)

merged_cbba.to_csv('data/merged_cbba.csv', index=False)
print('merged cbba csvs')