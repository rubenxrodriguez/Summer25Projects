import pandas as pd

df_net = pd.read_csv("composite_net_rankings.csv")
df_srs = pd.read_csv("composite_srs_rankings.csv")

print("="*30)
print('-'*10,'Analysis of Net vs SRS Rankings','-'*10)
# Assuming df_net and df_srs are already loaded
comparison = df_net[['team', 'mean_rank', 'median_rank']].merge(
    df_srs[['team', 'mean_rank', 'median_rank']], 
    on='team', 
    suffixes=('_net', '_srs')
)


comparison['mean_rank_diff'] = comparison['mean_rank_net'] - comparison['mean_rank_srs']
comparison['median_rank_diff'] = comparison['median_rank_net'] - comparison['median_rank_srs']

print(comparison[['mean_rank_diff', 'median_rank_diff']].describe())
print('\n'*3)

print(comparison.sort_values('mean_rank_diff', key=abs, ascending=False).head(10))
print(comparison.sort_values('median_rank_diff', key=abs, ascending=False).head(10))
print('\n'*3)


print("Correlation between mean_rank_net and mean_rank_srs:",
      comparison['mean_rank_net'].corr(comparison['mean_rank_srs']))

print("Correlation between median_rank_net and median_rank_srs:",
      comparison['median_rank_net'].corr(comparison['median_rank_srs']))

print('\n'*3)

mean_diff_std = comparison['mean_rank_diff'].std()
mean_diff_mean = comparison['mean_rank_diff'].mean()
outliers = comparison[abs(comparison['mean_rank_diff'] - mean_diff_mean) > 2 * mean_diff_std]
print("Mean rank outliers:")
print(outliers[['team', 'mean_rank_net', 'mean_rank_srs', 'mean_rank_diff']])