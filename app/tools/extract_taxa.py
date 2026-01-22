'''
Extracts observations for Zootoca vivipara from iNaturalist data export.
'''

import pandas as pd

scientific_name = 'Falco rusticolus'
scientific_name = 'Bubo scandiacus'

print("Loading datafile")

# Load the CSV file
file_path = '../privatedata/inaturalist-suomi-20-observations.csv'

df = pd.read_csv(file_path)
print("Datafile loaded")

filtered_df = df[df['scientific_name'] == scientific_name]
print(f"Filtered: {len(filtered_df)} rows found")

# Save to new CSV file with all original columns
output_file_path = f'../privatedata/extracted_{scientific_name.replace(" ", "_")}.csv'
filtered_df.to_csv(output_file_path, index=False)

print(f"All done, file saved as {output_file_path}")

