import os
import pandas as pd
import numpy as np

# Configuration
file_path = "net_files"
season_years = ['20_21', '21_22', '22_23', '23_24', '24_25']  # Matching your file names
weights = [0.10, 0.15, 0.20, 0.25, 0.30]  # Weighting recent seasons more heavily

def process_srs_data(file_path):
    # Initialize a dictionary to hold all DataFrames
    all_data = {}
    
    # Read each CSV file and store with season as key
    for file in os.listdir(file_path):
        if file.endswith(".csv") and file.replace('.csv', '') in season_years:
            season = file.replace('.csv', '')
            file_name = os.path.join(file_path, file)
            
            # Read CSV, skipping empty columns (those with no header)
            df = pd.read_csv(file_name)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove empty columns
            df['Team'] = df['Team'].str.strip()
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            df.rename(columns={
                'net rank': 'rank',
                'Team': 'team'
            }, inplace=True)
            
            # Add season column and store in dictionary
            df['season'] = season
            all_data[season] = df[['team', 'rank', 'season']]
    
    # Combine all seasons into one DataFrame
    combined = pd.concat(all_data.values(), ignore_index=True)
    
    # Convert season to categorical to preserve order
    combined['season'] = pd.Categorical(combined['season'], categories=season_years, ordered=True)
    
    # Normalize rankings within each season to account for different numbers of teams
    combined['normalized_rank'] = combined.groupby('season')['rank'].transform(
        lambda x: (x - 1) / (x.max() - 1) * 100  # Scale to 0-100 range (0 = best)
    )
    
    return combined

def calculate_weighted_averages(combined_df, weights):
    # Create a weight mapping
    weight_map = {season: weight for season, weight in zip(season_years, weights)}
    # Ensure we're working with numeric types
    combined_df['normalized_rank'] = combined_df['normalized_rank'].astype(float)
    
    # Add weight column (convert to float if not already)
    combined_df['weight'] = combined_df['season'].map(weight_map).astype(float)
    
    # Group by team and calculate summary statistics, including std
    team_stats = combined_df.groupby('team').agg({
        'rank': ['mean', 'median', 'min', 'max', 'count', 'std'],
        'normalized_rank': 'mean',
    })
    
    # Flatten multi-index columns
    team_stats.columns = ['_'.join(col).strip() for col in team_stats.columns.values]
    
    # Rename columns for clarity
    team_stats = team_stats.rename(columns={
        'rank_mean': 'mean_rank',
        'rank_median': 'median_rank',
        'rank_min': 'best_rank',
        'rank_max': 'worst_rank',
        'rank_count': 'seasons_count',
        'rank_std': 'rank_stddev',
        'normalized_rank_mean': 'mean_normalized_rank'
    })
    
    # Sort by composite score (higher is better)
    team_stats = team_stats.sort_values('median_rank', ascending=True)
    
    # Add overall rank (1 = best)
    team_stats['median_rank'] = range(1, len(team_stats) + 1)
    
    # Calculate stability score (lower std = more consistent performance)
    rank_std = combined_df.groupby('team')['rank'].std().rename('rank_stability')
    team_stats = team_stats.join([rank_std])
    # Round all numeric columns to 1 decimal
    team_stats = team_stats.round(1)
    return team_stats

# Process the data
combined_data = process_srs_data(file_path)
weighted_averages = calculate_weighted_averages(combined_data, weights)

# Save results
weighted_averages.to_csv('conf_net_0910.csv')

# Display top 20 teams
print(weighted_averages.head(20).round(2))
