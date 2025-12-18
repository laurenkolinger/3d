import Metashape
import os, sys, time, math
import pandas as pd
import config

# this script : 
# 1. aligns photos
# 2. removes points with high reconstruction uncertainty
# 3. optimizes cameras
# 4. removes points with high reprojection error
# 5. removes points with high projection accuracy
# 6. rotates the coordinate system to the bounding box
# 7. builds dense cloud
# 8. builds model
# 9. smooths model
# 10. builds UV
# 11. builds texture
# 12. generates report
# 13. saves the project

# Ensure paths are initialized
config.set_paths()

# Load parameters from configuration
recunc = config.PROCESSING_PARAMS["step1"]["reconstruction_uncertainty"]
reperr = config.PROCESSING_PARAMS["step1"]["reprojection_error"]
projacc = config.PROCESSING_PARAMS["step1"]["projection_accuracy"]
downscal = config.PROCESSING_PARAMS["step1"]["downscale_factor"]
doc = Metashape.app.document

# Make sure output directories exist
config.create_output_directories()

# Get report directory from configuration
report_dir = config.PATHS["initial_reports"]

# Initialize or read the CSV tracking file
try:
    df = pd.read_csv(config.METADATA_CSV)
    
    # If the project is new (no chunks), check if we should add photos based on CSV
    if len(doc.chunks) == 0:
        # Get PSX file path
        psx_path = doc.path
        if psx_path:
            psx_name = os.path.basename(psx_path)
            psx_dir = os.path.dirname(psx_path)
            
            # Update CSV with this PSX info if it's not already there
            for index, row in df.iterrows():
                if pd.isna(row.get('psxraw_path')) or pd.isna(row.get('psxraw_name')):
                    df.at[index, 'psxraw_path'] = psx_dir
                    df.at[index, 'psxraw_name'] = psx_name
            
            # Check if any rows have extracted frames but no photos added to PSX
            for index, row in df.iterrows():
                if row.get('extract_frames_complete') == 'Yes' and pd.isna(row.get('step1_complete')):
                    frames_dir = row.get('frames_dir')
                    if frames_dir and os.path.exists(frames_dir):
                        # Create a new chunk for this transect
                        transect_id = row.get('transect_id')
                        if transect_id:
                            chunk = doc.addChunk()
                            chunk.label = transect_id
                            
                            # Add photos to the chunk
                            photo_files = []
                            for ext in ['.tif', '.tiff', '.TIF', '.TIFF']:
                                photo_files.extend([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(ext)])
                            
                            if photo_files:
                                chunk.addPhotos(photo_files)
                                print(f"Added {len(photo_files)} photos for transect {transect_id}")
            
            # Save the document with added photos
            doc.save()
            
            # Update the CSV
            df.to_csv(config.METADATA_CSV, index=False)
except Exception as e:
    print(f"Error reading or initializing tracking CSV: {e}")
    # Continue with the script even if CSV operations fail
    pass

for chunk in doc.chunks:
    
    #align photos and make sparse point cloud
    chunk.matchPhotos(downscale = 1, keypoint_limit = 40000, tiepoint_limit = 4000, generic_preselection = True, reference_preselection = True, filter_stationary_points = False)
    chunk.alignCameras(adaptive_fitting=True)
    doc.save()
    
    # Select cameras that were not aligned initially
    unaligned_cameras = [camera for camera in chunk.cameras if not camera.transform]

    # Reset the alignment for the unaligned cameras
    for camera in unaligned_cameras:
        camera.transform = None

    # Attempt to align the unaligned cameras
    chunk.alignCameras(cameras=unaligned_cameras, reset_alignment=False)

    # Reset the region
    chunk.resetRegion()

    # Save the project
    doc.save()
    
    #gradual seln: reconstruction uncertainty
    f1 = Metashape.TiePoints.Filter()
    f1.init(chunk, Metashape.TiePoints.Filter.ReconstructionUncertainty)
    f1.removePoints(recunc)

    #optimize cameras
    chunk.optimizeCameras(fit_k4=True, adaptive_fitting=True)
    
    #reprojection error
    f2 = Metashape.TiePoints.Filter()
    f2.init(chunk, Metashape.TiePoints.Filter.ReprojectionError)
    f2.removePoints(reperr)
    
    #projection accuracy
    f = Metashape.TiePoints.Filter()
    f.init(chunk, Metashape.TiePoints.Filter.ProjectionAccuracy)
    f.removePoints(projacc)
    
    # Save the project
    doc.save()

    #rotate coordinate system to bounding box
    R = chunk.region.rot     # Bounding box rotation matrix
    C = chunk.region.center  # Bounding box center vector

    if chunk.transform.matrix:
        T = chunk.transform.matrix
        s = math.sqrt(T[0, 0] ** 2 + T[0, 1] ** 2 + T[0, 2] ** 2)  # scaling # T.scale()
        S = Metashape.Matrix().Diag([s, s, s, 1])                  # scale matrix
    else:
        S = Metashape.Matrix().Diag([1, 1, 1, 1])

    T = Metashape.Matrix([[R[0, 0], R[0, 1], R[0, 2], C[0]],
                          [R[1, 0], R[1, 1], R[1, 2], C[1]],
                          [R[2, 0], R[2, 1], R[2, 2], C[2]],
                          [0, 0, 0, 1]])

    chunk.transform.matrix = S * T.inv()
    
    #build dense cloud
    chunk.buildDepthMaps(downscale=downscal)
    chunk.buildDenseCloud()
    doc.save()
    
    #build mesh
    chunk.buildModel(surface_type=Metashape.Arbitrary, interpolation=Metashape.EnabledInterpolation)
    
    #builds texture
    chunk.buildUV(mapping_mode=Metashape.GenericMapping)
    chunk.buildTexture(texture_size=4096, texture_type=Metashape.Model.DiffuseMap)
    doc.save()
    
    # Generate report
    chunk_label = chunk.label
    report_path = os.path.join(report_dir, f"{chunk_label}_report.pdf")
    chunk.exportReport(report_path)
    
    # Update tracking CSV
    try:
        df = pd.read_csv(config.METADATA_CSV)
        # Find the row for this chunk
        matching_rows = df[df['transect_id'] == chunk_label]
        if not matching_rows.empty:
            index = matching_rows.index[0]
            df.at[index, 'step1_complete'] = 'Yes'
            df.to_csv(config.METADATA_CSV, index=False)
            print(f"Updated CSV tracking for {chunk_label}")
    except Exception as e:
        print(f"Error updating tracking CSV: {e}")

print("Processing completed successfully")
