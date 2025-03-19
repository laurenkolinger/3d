import Metashape
import os
import pandas as pd

# Set the desired number of vertices for decimation
nverts = 3000000  # Set the desired number of vertices here
sketchfab_api_token = "152b6186db06477482e2b42b327541da"  # Replace with your Sketchfab API token

# Open the existing project
doc = Metashape.app.document

# Get the directory one level above the project directory and read in the csv. 
project_dir = os.path.dirname(doc.path)
template_dir = os.path.join(project_dir, "../..")
csv_file_path = os.path.join(template_dir, "00_list.csv")

# Read the CSV file
df = pd.read_csv(csv_file_path)

# Iterate over unique values of `psx_finalname` in the CSV
for destination in df['psx_finalname'].unique():
        
    # Get the directory and file paths from the CSV
    matching_rows = df.loc[df['psx_finalname'] == destination]
    
    final_dir = df.loc[df['psx_finalname'] == destination, 'psx_finaldir'].values[0]
    dest_project_path = os.path.join(template_dir, final_dir, destination)

    # Check if the project exists, and open it if it does
    if os.path.exists(dest_project_path):
        doc = Metashape.Document()
        doc.open(dest_project_path, read_only=False)
        print(f"Opened project: {dest_project_path}")
    else:
        print(f"Project not found: {dest_project_path}")
        continue
    
    # Get the project directory
    project_dir = os.path.dirname(doc.path)
    
    # Iterate over each chunk in the project
    for chunk in doc.chunks:
        
        # Duplicate the chunk and name it with a `_temp` suffix
        temp_chunk = chunk.copy()
        temp_chunk.label = f"{chunk.label}_temp"

        # Decimate the duplicated chunk to the specified number of vertices
        temp_chunk.decimateModel(face_count=nverts)
        print(f"Decimated {temp_chunk.label} to {nverts} vertices.")
        
        # Check if the chunk needs to be re-textured (required after decimation if textures are used)
        if not temp_chunk.model.hasTextures():
            temp_chunk.buildTexture(texture_size=4096, texture_type=Metashape.Model.DiffuseMap)
            print(f"Re-textured {temp_chunk.label} after decimation.")

        # Use publishData to upload the decimated model to Sketchfab
        publish_task = Metashape.Tasks.PublishData()
        publish_task.service = Metashape.ServiceType.ServiceSketchfab
        publish_task.source_data = Metashape.DataSource.ModelData
        publish_task.title = f"Model: {chunk.label}"
        publish_task.description = "generated using Metashape."
        publish_task.tags = "3D, model, Metashape, coralreef, "
        publish_task.token = sketchfab_api_token
        publish_task.is_draft = True  # Set to True if you don't want the model published immediately
        publish_task.is_private = False  # Set to True if you want the model to be private
        publish_task.tile_size = 256
        publish_task.min_zoom_level = -1
        publish_task.max_zoom_level = -1

        # Apply the publish task to the temp chunk
        publish_task.apply(temp_chunk)
        print(f"Model {temp_chunk.label} uploaded using publishData.")

        # Delete the temporary chunk
        doc.remove(temp_chunk)
        print(f"Temporary chunk {temp_chunk.label} deleted after upload.")

    print(f"Processing completed for project: {destination}")

print("All processing completed successfully.")
