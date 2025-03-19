import Metashape
import os, sys, time, math

# REDUNDANT WITH STEP 1 - REmove? 
# this script: 
# 1. builds depth maps
# 2. builds dense cloud
# 3. builds model
# 4. smooths model
# 5. builds UV
# 6. builds texture

# the amount by which you want to divide the mesh face count by 
# div_factor = 8 

# Open the existing project
doc = Metashape.app.document

# Get the directory one level above the project directory and create the "reports" folder
project_dir = os.path.dirname(doc.path)
report_dir = os.path.join(project_dir, "..", "04_reports_initial")

# Ensure the report directory exists
os.makedirs(report_dir, exist_ok=True)

# print(f"{report_dir}")

for chunk in doc.chunks:
    # Build dense cloud
    chunk.buildDepthMaps(
        downscale=1,
        filter_mode=Metashape.NoFiltering
    )
    #chunk.buildDenseCloud()
    
    # Build model
    chunk.buildModel(
        source_data=Metashape.DepthMapsData,
        surface_type=Metashape.Arbitrary,
        face_count=Metashape.MediumFaceCount,
        volumetric_masks=False,
        interpolation=Metashape.EnabledInterpolation,
        vertex_colors=True
    )
    
    # Smooth model
    #chunk.smoothModel(
    #    strength=3,
    #    apply_to_selection=False,
    #    fix_borders=True,
    #    preserve_edges=False
    #)
    
    # face_ct = len(chunk.model.faces) 
    # target_face_count = int(original_face_count / div_factor)
    # 
    # # Decimate model
    # chunk.decimateModel(
    #     face_count=target_face_count,
    #     apply_to_selection=False
    # )
    
    
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
