'''
2023-12-05
This script takes raw iNaturalist data export observation file, and converts it into format that can be used by synchronization scrips. It removes unnecessary rows and columns.
'''

import pandas as pd

print("Loading datafile")

# Load the CSV file
file_path = '../privatedata/inaturalist-suomi-20-observations.csv'

df = pd.read_csv(file_path)
print("Datafile loaded")

# Filtering the DataFrame
filtered_df = df[
    (df['coordinates_obscured'] == True) & 
    ((df['place_country_name'] == 'Finland') | (df['place_country_name'] == 'Åland')) &
    (df['private_latitude'].notna())
]
print("Filtered")

# Selecting specific columns
selected_columns = [
    'id',
    'observed_on',
    'positional_accuracy',
    'private_place_guess', 
    'private_latitude',
    'private_longitude'
]

filtered_selected_df = filtered_df[selected_columns]
print("Columns selected")

# Replacing semicolons with commas
filtered_selected_df_replaced = filtered_selected_df.replace(to_replace=';', value=',', regex=True)
print("Replacements done")

# Save as TSV file
output_file_path = '../privatedata/latest.tsv'
filtered_selected_df_replaced.to_csv(output_file_path, sep='	', index=False)

print(f"All done, file saved as {output_file_path}")
