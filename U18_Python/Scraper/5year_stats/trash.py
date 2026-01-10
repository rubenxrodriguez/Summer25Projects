import pandas as pd

df = pd.read_csv("5year_stats/composite_srs_rankings.csv")
df = df[['team','mean_rank','median_rank','most_common_conference','rank_stability']]
df.to_csv("5year_stats/composite_srs_rankings2.csv", index=False)

# Load team names from composite rankings
team_df = pd.read_csv("composite_srs_rankings2.csv")
team_names = team_df['team'].unique()