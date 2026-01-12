import pandas as pd
import os

# Define the list of teams you're interested in
teams_list = [
    "Portland Pilots",
    "Pepperdine Waves",
    "Pacific Tigers",
    "Santa Clara Broncos",
    "Saint Mary's Gaels",
    "San Francisco Dons",
    "San Diego Toreros",
    "Washington State Cougars",
    "Oregon State Beavers",
    "Gonzaga Bulldogs",
    "Loyola Marymount Lions",
    "Seattle Redhawks"
]
user_team = "Loyola Marymount Lions"
print('\n'*20)

folder = "LMU"
# Loop through each file in the file paths
for file_name in os.listdir(folder):
    if file_name.endswith('.csv'):
        full_path = os.path.join(folder, file_name)
    # Load the CSV file

    df = pd.read_csv(full_path, sep=',')
    
    # Filter the DataFrame to only include rows where 'Team' is in the teams_list
    df_filtered = df[df['Team'].isin(teams_list)]
    
    # Sort the filtered DataFrame by 'PPP' in descending order
    df_sorted = df_filtered.sort_values(by='%Time', ascending=False)
    
    # Highlight the user team
    df_sorted['Highlight'] = df_sorted['Team'].apply(lambda x: 'Yes' if x == user_team else '   ')



     #Move the 'Highlight' column to the third position
    # Get the list of columns
    cols = df_sorted.columns.tolist()

    # Remove 'Highlight' from the list (if it exists)
    if 'Highlight' in cols:
        cols.remove('Highlight')

    # Insert 'Highlight' at the third position (index 2)
    cols.insert(2, 'Highlight')

    removecols = ['Eligibility Year', 'Height']
    for col in removecols:
        if col in cols:
            cols.remove(col)
    # Reorder the DataFrame
    df_sorted = df_sorted[cols]
    df_sorted = df_sorted.sort_values(by=['Poss'],ascending = True)

    # Reset index if desired (optional)
    df_sorted.reset_index(drop=True, inplace=True)
    
    # Display or save the sorted DataFrame
    print(f"Results for {file_name}:")
    print(df_sorted,'\n')
    
    # To save the sorted data to a new CSV
    # Output file name based on the input file
    #output_file = file_name.replace(".csv", "_filtered_sorted.csv")
    #df_sorted.to_csv(output_file, index=False)
    #print(f"Saved to {output_file}")

#draw a scatter. find an elite region. so teams have to be above ppp and time%