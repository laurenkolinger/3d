"""
Step 2: Chunk Management and Consolidation

This script automates the process of copying chunks between Metashape projects based on
tracking data. It reads data on processed transects, appends chunks from source
projects to destination projects, and saves the results.
"""

import os
import logging
import Metashape
import pandas as pd
from config import (
    DIRECTORIES,
    PROJECT_NAME,
    get_tracking_files,
    update_tracking,
    PARAMS,
    TIMESTAMP
)
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["logs"], f"step2_{PROJECT_NAME}_{TIMESTAMP}.log")),
        logging.StreamHandler()
    ]
)

def main():
    """Main function to manage chunks across projects."""
    # Open the existing document if running in Metashape GUI
    if Metashape.app.document:
        doc = Metashape.app.document
    else:
        doc = Metashape.Document()
    
    # Define start and final directories for PSX files
    psx_startdir = DIRECTORIES["psx_input"]
    psx_finaldir = DIRECTORIES["psx_output"]
    
    # Create the output directory if it doesn't exist
    os.makedirs(psx_finaldir, exist_ok=True)
    
    # Get the project directory
    project_dir = DIRECTORIES["base"]
    
    # Check for tracking files
    tracking_files = get_tracking_files()
    
    if not tracking_files:
        logging.error("No tracking files found. Run step1.py first to generate tracking data.")
        return
    
    # Create or load tracking DataFrame
    df = pd.DataFrame()
    for tracking_file in tracking_files:
        tracking_data = pd.read_csv(tracking_file)
        df = pd.concat([df, tracking_data])
    
    # Filter for completed Step 1 transects
    completed_transects = df[df["Step 1 complete"].astype(str) == "True"]
    
    if completed_transects.empty:
        logging.error("No completed transects found. Run step1.py first.")
        return
    
    # Extract site information from transect IDs
    # Assuming format like TCRMP20241014_3D_BWR_T1 where BWR is site and T1 is transect number
    completed_transects["site"] = completed_transects["Model ID"].str.split("_").str[2]
    completed_transects["transect"] = completed_transects["Model ID"].str.split("_").str[3]
    completed_transects["prefix"] = completed_transects["Model ID"].str.split("_").str[:3].str.join("_")
    
    # Formulate chunk names, source and destination paths
    completed_transects["chunk_name"] = completed_transects["Model ID"]
    completed_transects["psx_startdir"] = psx_startdir
    completed_transects["psx_finaldir"] = psx_finaldir
    completed_transects["psx_finalname"] = completed_transects["prefix"] + ".psx"
    completed_transects["psx_startname"] = completed_transects["PSX file"].apply(os.path.basename)
    
    # Save the updated information back to the tracking files
    for tracking_file in tracking_files:
        transect_id = os.path.basename(tracking_file).replace("_tracking.csv", "")
        transect_data = completed_transects[completed_transects["Model ID"] == transect_id]
        if not transect_data.empty:
            transect_data.to_csv(tracking_file, index=False)
    
    # Iterate over each unique destination
    for destination in completed_transects["psx_finalname"].unique():
        # Create or open the destination .psx project
        dest_project_path = os.path.join(psx_finaldir, destination)
        dest_doc = Metashape.Document()
        
        if os.path.exists(dest_project_path):
            logging.info(f"Opening existing project: {dest_project_path}")
            dest_doc.open(dest_project_path, read_only=False)
        else:
            logging.info(f"Creating new project: {dest_project_path}")
            dest_doc.save(dest_project_path)  # Create a new project file
        
        # Filter the rows that correspond to this destination
        relevant_transects = completed_transects[completed_transects["psx_finalname"] == destination]
        
        # Iterate over each row and append the corresponding chunk from the origin .psx
        for _, row in relevant_transects.iterrows():
            origin_project_path = os.path.join(psx_startdir, row["psx_startname"])
            origin_doc = Metashape.Document()
            
            try:
                logging.info(f"Opening source project: {origin_project_path}")
                origin_doc.open(origin_project_path, read_only=True)
                final_chunk_label = row["Model ID"]
                current_model_id = row["Model ID"]
                site_name = row["site"]
                
                # Find the chunk by name in the origin project
                chunk = next((ch for ch in origin_doc.chunks if ch.label == row["chunk_name"]), None)
                
                if chunk is not None:
                    logging.info(f"Appending chunk: {chunk.label} from {origin_project_path} to {destination}")
                    # Check if a chunk with this label already exists in the destination
                    existing_chunk = next((ch for ch in dest_doc.chunks if ch.label == final_chunk_label), None)
                    
                    if existing_chunk is not None:
                        logging.warning(f"Chunk {final_chunk_label} already exists in {destination}. Skipping.")
                        update_tracking(current_model_id, {
                            "Status": "Step 2 - Chunk skipped",
                            "Step 2 complete": "True",
                            "Step 2 site": site_name,
                            "Notes": f"Chunk {final_chunk_label} already exists in {destination}. Skipped."
                        })
                        continue
                    
                    # Append the chunk directly to the destination project
                    chunk.label = final_chunk_label
                    dest_doc.append(origin_doc, [chunk])
                    update_tracking(current_model_id, {
                        "Status": "Step 2 complete",
                        "Step 2 complete": "True",
                        "Step 2 site": site_name,
                        "Notes": f"Chunk {final_chunk_label} appended to {destination}."
                    })
                else:
                    logging.error(f"Chunk {row['chunk_name']} not found in {origin_project_path}")
                    update_tracking(current_model_id, {
                        "Status": "Error in Step 2 - Chunk not found",
                        "Step 2 complete": "False",
                        "Step 2 site": site_name,
                        "Notes": f"Chunk {row['chunk_name']} not found in {origin_project_path}"
                    })
            except Exception as e:
                logging.error(f"Error processing {origin_project_path} for transect {row['Model ID']}: {str(e)}")
                update_tracking(row['Model ID'], {
                    "Status": "Error in Step 2",
                    "Step 2 complete": "False",
                    "Step 2 site": row["site"],
                    "Notes": f"Error consolidating chunk for {row['Model ID']} from {origin_project_path}: {str(e)}"
                })
                continue
        
        # Save the destination project after appending all chunks
        logging.info(f"Saving project: {dest_project_path}")
        dest_doc.save(dest_project_path)
        logging.info(f"Chunks appended to {destination} and saved.")
    
    logging.info("All chunk management operations completed successfully.")

if __name__ == "__main__":
    main() 