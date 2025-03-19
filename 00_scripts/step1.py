import Metashape
import os, sys, time, math

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

# threshold = 0 # the threshold of quality below which to remove images 
recunc = 50 # reconstruction uncertainty threshold
reperr = 1 # reprojection error threshold
projacc = 10 # projection accuracy threshold 
downscal = 2 # downscale factor for depth map quality (1 - Ultra high, 2 - High, 4 - Medium, 8 - Low, 16-Lowest).
doc = Metashape.app.document

# Get the directory one level above the project directory and create the "reports" folder
project_dir = os.path.dirname(doc.path)
report_dir = os.path.join(project_dir, "..", "04_reports_initial")

# Ensure the report directory exists
os.makedirs(report_dir, exist_ok=True)

for chunk in doc.chunks:
    
    #disable images with quality < threshold    
    # chunk.analyzeImages()
    # for i in range(0, len(chunk.cameras)):
    # 	print(i)
    # 	camera = chunk.cameras[i]
    # 	print(camera)
    # 	quality = camera.frames[0].meta["Image/Quality"]
    # 	print(quality)
    # 	if float(quality) < threshold:
    # 		camera.enabled = False
    # doc.save()
    # 
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
                          [      0,       0,       0,    1]])

    chunk.transform.matrix = S * T.inv()  # resulting chunk transformation matrix
    doc.save()

# print(f"{report_dir}")

for chunk in doc.chunks:
    # Build dense cloud
    chunk.buildDepthMaps(
        downscale=4,
        filter_mode=Metashape.NoFiltering
    )
    #chunk.buildDenseCloud()
    
    # Build model
    chunk.buildModel(
        source_data=Metashape.DepthMapsData,
        surface_type=Metashape.Arbitrary,
        face_count=Metashape.HighFaceCount,
        volumetric_masks=False,
        interpolation=Metashape.EnabledInterpolation,
        vertex_colors=True
    )
    
    # Smooth model
    chunk.smoothModel(
        strength=3,
        apply_to_selection=False,
        fix_borders=True,
        preserve_edges=False
    )
    
    ## # Decimate model
    ## chunk.decimateModel(
    ##     face_count=2000000,
    ##     apply_to_selection=False
    ## )
    #
    
    # Build UV
    chunk.buildUV(
        mapping_mode=Metashape.GenericMapping,
        texture_size=16384,
        page_count=4
    )

    # Build texture
    chunk.buildTexture(
        texture_size=16384,
        texture_type=Metashape.Model.DiffuseMap,
        blending_mode=Metashape.MosaicBlending,
        fill_holes=True,
        ghosting_filter=True,
        enable_gpu=False,
        relaxed_precision=True
    )

    ## Remove lighting
    #chunk.removeLighting(
    #    color_mode=Metashape.SingleColor,
    #    ao_map_path="",
    #    internal_blur_radius=1.5,
    #    mesh_noise_suppression=True,
    #    ao_multiplier=1.5
    #)
    
    # Generate report
    report_file_path = os.path.join(report_dir,f"{chunk.label}.pdf")
    chunk.exportReport(report_file_path, title = f"{chunk.label}.pdf")
    
    # Save the project
    doc.save()

print("Processing completed successfully.")
