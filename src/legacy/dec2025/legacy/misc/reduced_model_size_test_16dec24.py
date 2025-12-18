import Metashape
import os

def export_model_with_reductions(chunk, output_dir, label, face_reduction_factor, texture_size):
    # Duplicate the active chunk
    # original_chunk = chunk
    # new_chunk = doc.addChunk()
    # new_chunk.addFrames(original_chunk, copy_point_cloud=True, copy_model=True)
    # doc.chunk = new_chunk
    
    new_chunk = chunk.copy()
    
    # Get the model from the new chunk
    model = new_chunk.model

    if model is None:
        print("No model found in the chunk.")
        return

    # Get the current face count
    original_face_count = len(new_chunk.model.faces)
    print(f"Original face count: original_face_count")
    
    # Get model statistics to determine the original face count
    target_face_count = int(original_face_count * face_reduction_factor)
    
    # Decimate the model to reduce face count
    print(f"Reducing face count to {target_face_count}...")
    chunk.decimateModel(face_count=target_face_count)
    
    # Rebuild UV mapping
    print("Rebuilding UV mapping...")
    new_chunk.buildUV(mapping_mode=Metashape.GenericMapping)
    
    # Rebuild texture with reduced size
    print(f"Rebuilding texture with size {texture_size}...")
    new_chunk.buildTexture(
        texture_size=texture_size,
        texture_type=Metashape.Model.DiffuseMap,
        blending_mode=Metashape.MosaicBlending,
        fill_holes=True,
        ghosting_filter=True,
        enable_gpu=False,
        relaxed_precision=True
    )    
    
    # Export the reduced model
    model_file_path = os.path.join(output_dir, f"{label}_faces{target_face_count}_tex{texture_size}.obj")
    new_chunk.exportModel(
        path=model_file_path,
        format=Metashape.ModelFormatOBJ,
        texture_format=Metashape.ImageFormatTIFF,
        save_texture=True
    )
    
    print(f"Exported reduced model: {model_file_path}")    

# Open the Metashape document
doc = Metashape.app.document

# Ensure a document is opened and has at least one chunk
if len(doc.chunks) == 0:
    print("No chunks found. Please open a document with at least one chunk.")
    exit()

# Get the active chunk
chunk = doc.chunk

# Define output directory for reduced models
output_dir = os.path.join(os.path.dirname(doc.path), "reduced_models")
os.makedirs(output_dir, exist_ok=True)

# Define reduction parameters (face reduction factors and texture sizes)
face_reduction_factors = [0.25, 0.5, 1]  # Reduce to 50%, 25%, and 10% of original faces
texture_sizes = [2048, 4096, 8192] # Texture sizes to try (in pixels)

og_chunk = chunk 

# Iterate through combinations of reductions
for texture_size in texture_sizes:
    for face_reduction_factor in face_reduction_factors:
        label = f"reduced_model_{int(face_reduction_factor * 100)}percent"
        export_model_with_reductions(og_chunk, output_dir, label, face_reduction_factor, texture_size)

print("All reduced models exported successfully.")
