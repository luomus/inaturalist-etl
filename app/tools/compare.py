# Script that loads two data files, and outputs identifiers that exist in finbif-file but not in the inat-file.

import pandas as pd

finbif_file = "../privatedata/occurrences.txt"
inat_file = "../privatedata/inaturalist-suomi-20-observations.csv"
output_file = "../privatedata/ids_to_be_deleted.csv"

# Prefix to remove from finbif identifiers
PREFIX_TO_REMOVE = "http://tun.fi/HR.3211/"

print("Loading identifiers from inat_file...")
# Load all identifiers from inat_file into a set for fast lookup
inat_df = pd.read_csv(inat_file, sep=',', usecols=['id'])
inat_ids = set(inat_df['id'].astype(str).dropna())
print(f"Loaded {len(inat_ids)} identifiers from inat_file")

print("Processing finbif_file in chunks...")
# Process finbif_file in chunks to handle large files efficiently
chunk_size = 100000
ids_to_delete = []

with pd.read_csv(finbif_file, sep='\t', usecols=['parentEventID'], chunksize=chunk_size, skiprows=[1, 2]) as reader:
    for chunk_num, chunk in enumerate(reader):
        # Extract identifiers and remove prefix
        chunk_ids = chunk['parentEventID'].astype(str).dropna()
        # Remove the prefix from each identifier
        chunk_ids = chunk_ids.str.replace(PREFIX_TO_REMOVE, '', regex=False)
        
        # Find identifiers that exist in finbif but not in inat
        missing_ids = chunk_ids[~chunk_ids.isin(inat_ids)]
        ids_to_delete.extend(missing_ids.tolist())
        
        if (chunk_num + 1) % 10 == 0:
            print(f"Processed {(chunk_num + 1) * chunk_size:,} rows, found {len(ids_to_delete):,} missing identifiers so far")

print(f"\nTotal identifiers to delete: {len(ids_to_delete):,}")

# Write results to CSV
print(f"Writing results to {output_file}...")
output_df = pd.DataFrame({'id': ids_to_delete})
output_df.to_csv(output_file, index=False)

print(f"Done! Results written to {output_file}")
