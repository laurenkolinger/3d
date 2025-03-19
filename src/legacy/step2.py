import Metashape
import os
import pandas as pd
import config

# This script automates the process of copying chunks between Metashape projects based on a CSV file. It reads the CSV, appends chunks from source projects to destination projects, and saves the results. Key steps include:
# 
# -   read the CSV file location:
# 
# -   Project handling: For each unique project name in the CSV, the script opens or creates a destination .psx project and appends chunks from specified source projects.
# 
# -   Chunk copying: It searches for the specified chunk in the source project and appends it to the destination project.
# 
# -   Saving results: After processing, the destination project is saved, ensuring all chunks are properly appended.

# Open the existing project
doc = Metashape.app.document

# Get input and output directories from configuration
psx_startdir = config.INPUT_DIRS["psx_input"]
psx_finaldir = config.OUTPUT_DIRS["psx_output"]

# Get metadata CSV file path
csv_file_path = config.METADATA_CSV

# Read the CSV file
df = pd.read_csv(csv_file_path)

# Split the filename by underscore
df[['site', 'transect']] = df['filename'].str.split('_', expand=True)[[2, 3]]

# For the prefix, we need to combine the first three elements
df['prefix'] = df['filename'].str.split('_').str[:3].str.join('_')

# write chunk name 
# df['chunk_name'] = df['site']+'_'+df['transect']
df['chunk_name'] = df['filename']

df['psx_startdir'] = os.path.relpath(psx_startdir, os.path.dirname(csv_file_path))
df['psx_finaldir'] = os.path.relpath(psx_finaldir, os.path.dirname(csv_file_path))
df['psx_finalname'] = df['prefix']+'.psx'

# Write the updated DataFrame back to the same CSV file
df.to_csv(csv_file_path, index=False)

# Iterate over each unique destination
for destination in df['psx_finalname'].unique():
    # Create or open the destination .psx project
    dest_project_path = os.path.join(psx_finaldir, destination)
    dest_doc = Metashape.Document()
    
    if os.path.exists(dest_project_path):
        dest_doc.open(dest_project_path, read_only=False)
    else:
        dest_doc.save(dest_project_path)  # Create a new project file
    
    # Filter the rows that correspond to this destination
    rows = df[df['psx_finalname'] == destination]
    
    # Iterate over each row and append the corresponding chunk from the origin .psx
    for _, row in rows.iterrows():
        print(row)
        origin_project_path = os.path.join(psx_startdir, row['psx_startname'])
        origin_doc = Metashape.Document()
        origin_doc.open(origin_project_path, read_only=True)
        finalchunklab = row['filename']
        
        # Find the chunk by name in the origin project
        chunk = next((ch for ch in origin_doc.chunks if ch.label == row['chunk_name']), None)
        
        if chunk is not None:
            print(f"Appending chunk: {chunk.label} from {origin_project_path} to {destination}")
            # Append the chunk directly to the destination project
            chunk.label = finalchunklab
            dest_doc.append(origin_doc, [chunk])
        else:
            print(f"Chunk {row['chunk_name']} not found in {origin_project_path}")
    
    # Save the destination project after appending all chunks
    dest_doc.save(dest_project_path)
    print(f"Chunks appended to {destination} and saved.")

print("All processing completed successfully.")
