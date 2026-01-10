import pandas as pd
from collections import defaultdict

# Load data
srs_teams = set(pd.read_csv('composite_srs_rankings.csv')['team'])
net_teams = set(pd.read_csv('composite_net_rankings.csv')['team'])
current_data = pd.read_csv('srs_files/24_25.csv')

# Create conference lookup
conf_lookup = dict(zip(current_data['School'], current_data['Conf']))

# Step 1: Group name variations
name_groups = defaultdict(list)

# Manual grouping for known cases
manual_groups = {
    "Loyola Marymount": ["Loyola-Marymount","LMU"],
    "North Carolina A&T": ["NC A&T"],
    "North Carolina": ["UNC"]
}

# Auto-detect similar names (using your files)
all_names = sorted(srs_teams.union(net_teams))
for name in all_names:
    matched = False
    # Check manual groups first
    for std_name, aliases in manual_groups.items():
        if name == std_name or name in aliases:
            name_groups[std_name].append(name)
            matched = True
            break
    if not matched:
        name_groups[name].append(name)  # Start new group

# Step 2: Build final dictionary
normalization_dict = {}
for std_name, aliases in name_groups.items():
    # Remove duplicate aliases and the standard name itself
    unique_aliases = list(set(aliases) - {std_name})
    normalization_dict[std_name] = {
        "aliases": unique_aliases,
        "conference": conf_lookup.get(std_name, "Unknown")
    }
print(normalization_dict)

# Save to JSON
import json
with open('team_normalization.json', 'w') as f:
    json.dump(normalization_dict, f, indent=2)
'''
print("Sample output:")
print(json.dumps({
    "Loyola Marymount": normalization_dict["Loyola Marymount"],
    "North Carolina A&T": normalization_dict["North Carolina A&T"]
}, indent=2))
'''