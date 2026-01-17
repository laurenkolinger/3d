"""
Step 3: Dual Model Export (High-Poly and Low-Poly)

This script processes Scale=PASS models to generate production-ready outputs:
1. High-poly model export
2. Low-poly model creation (decimated + retextured)
3. Orthomosaic generation (full + tiled)
4. Report exports

Works on: processing/psxraw/*.psx files
Processes: Only chunks where Scale=PASS
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
    get_transect_status,
    PARAMS,
    TIMESTAMP
)
import datetime
import time
import shutil
from utility.file_naming import get_export_paths, clean_model_id

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DIRECTORIES["logs"], f"step3_dual_export_{PROJECT_NAME}_{TIMESTAMP}.log")),
        logging.StreamHandler()
    ]
)

def export_hipoly_model(chunk, model_id, base_output_dir, config):
    """
    Export high-poly model with texture.
    
    Args:
        chunk (Metashape.Chunk): The chunk to export
        model_id (str): Clean model ID
        base_output_dir (str): Base output directory
        config (dict): Export configuration
        
    Returns:
        bool: True if successful
    """
    try:
        paths = get_export_paths(model_id, base_output_dir)
        model_dir = paths['model']['dir']
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f"{model_id}_hipoly.obj")
        
        model_export_config = config['model_export']
        
        chunk.exportModel(
            path=model_path,
            binary=False,
            format=getattr(Metashape.ModelFormat, f"ModelFormat{model_export_config['format']}"),
            texture_format=getattr(Metashape.ImageFormat, f"ImageFormat{model_export_config['texture_format']}"),
            save_texture=model_export_config['save_texture'],
            save_uv=model_export_config['save_uv'],
            save_normals=model_export_config['save_normals'],
            save_colors=model_export_config['save_colors']
        )
        
        logging.info(f"High-poly model exported to: {model_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting high-poly model: {str(e)}")
        return False

def export_hipoly_report(chunk, model_id, base_output_dir):
    """
    Export high-poly processing report.
    
    Args:
        chunk (Metashape.Chunk): The chunk to export
        model_id (str): Clean model ID
        base_output_dir (str): Base output directory
        
    Returns:
        bool: True if successful
    """
    try:
        paths = get_export_paths(model_id, base_output_dir)
        report_dir = paths['report']['dir']
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"{model_id}_hipoly.pdf")
        
        chunk.exportReport(
            path=report_path,
            title=f"{model_id} - High Poly",
            description=f"High-resolution model export for {model_id}",
            page_numbers=True,
            include_system_info=True
        )
        
        logging.info(f"High-poly report exported to: {report_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting high-poly report: {str(e)}")
        return False

def create_lopoly_chunk(chunk, config):
    """
    Create low-poly version by duplicating, decimating, and retexturing.
    
    Args:
        chunk (Metashape.Chunk): Original chunk
        config (dict): Processing configuration
        
    Returns:
        tuple: (lopoly_chunk, cameras_removed) or (None, 0) on failure
    """
    try:
        logging.info("Duplicating chunk for low-poly processing (model only, no texture)...")
        # Copy only the model data, not texture (texture will be rebuilt after decimation)
        lopoly_chunk = chunk.copy(
            items=[Metashape.DataSource.ModelData],
            keypoints=False
        )
        lopoly_chunk.label = f"{chunk.label}_lopoly"
        
        stats = lopoly_chunk.model.statistics()
        current_faces = stats.faces
        decimation_factor = config['decimation_factor']
        target_faces = current_faces // decimation_factor
        
        logging.info(f"Decimating from {current_faces:,} to {target_faces:,} faces (factor: {decimation_factor})")
        lopoly_chunk.decimateModel(
            face_count=target_faces,
            apply_to_selection=False,
            replace_asset=True
        )
        
        cameras_before = sum(1 for cam in lopoly_chunk.cameras if cam.enabled)
        target_overlap = config['camera_overlap_reduction']['target_overlap']
        
        logging.info(f"Reducing camera overlap (target: {target_overlap} cameras per point)...")
        lopoly_chunk.reduceOverlap(
            overlap=target_overlap,
            use_selection=False
        )
        
        cameras_after = sum(1 for cam in lopoly_chunk.cameras if cam.enabled)
        cameras_removed = cameras_before - cameras_after
        logging.info(f"Camera overlap reduced: {cameras_before} → {cameras_after} ({cameras_removed} removed)")
        
        metashape_defaults = PARAMS['processing']['metashape']['defaults']
        
        logging.info("Rebuilding UV mapping...")
        lopoly_chunk.buildUV(
            mapping_mode=getattr(Metashape.MappingMode, metashape_defaults['mapping_mode']),
            page_count=metashape_defaults['page_count'],
            texture_size=metashape_defaults['texture_size']
        )
        
        # Check if we should use GPU for texture generation
        enable_texture_gpu = metashape_defaults.get("enable_texture_gpu", False)
        
        if not enable_texture_gpu:
            # Save current GPU state
            saved_gpu_mask = Metashape.app.gpu_mask
            saved_cpu_enable = Metashape.app.cpu_enable
            
            # Temporarily disable GPU for texture building
            Metashape.app.gpu_mask = 0
            Metashape.app.cpu_enable = True
            logging.info("GPU disabled for texture building (using CPU only)")
        
        logging.info("Rebuilding texture...")
        lopoly_chunk.buildTexture(
            blending_mode=getattr(Metashape.BlendingMode, metashape_defaults['blending_mode']),
            texture_size=metashape_defaults['texture_size'],
            fill_holes=metashape_defaults['fill_holes'],
            ghosting_filter=metashape_defaults['ghosting_filter']
        )
        
        if not enable_texture_gpu:
            # Restore GPU state for subsequent operations
            Metashape.app.gpu_mask = saved_gpu_mask
            Metashape.app.cpu_enable = saved_cpu_enable
            logging.info("GPU re-enabled after texture building")
        
        return lopoly_chunk, cameras_removed
        
    except Exception as e:
        logging.error(f"Error creating low-poly chunk: {str(e)}")
        return None, 0

def export_lopoly_model(lopoly_chunk, model_id, base_output_dir, config):
    """
    Export low-poly model with texture.
    
    Args:
        lopoly_chunk (Metashape.Chunk): The low-poly chunk to export
        model_id (str): Clean model ID
        base_output_dir (str): Base output directory
        config (dict): Export configuration
        
    Returns:
        bool: True if successful
    """
    try:
        paths = get_export_paths(model_id, base_output_dir)
        model_dir = paths['model']['dir']
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f"{model_id}_lopoly.obj")
        
        model_export_config = config['model_export']
        
        lopoly_chunk.exportModel(
            path=model_path,
            binary=False,
            format=getattr(Metashape.ModelFormat, f"ModelFormat{model_export_config['format']}"),
            texture_format=getattr(Metashape.ImageFormat, f"ImageFormat{model_export_config['texture_format']}"),
            save_texture=model_export_config['save_texture'],
            save_uv=model_export_config['save_uv'],
            save_normals=model_export_config['save_normals'],
            save_colors=model_export_config['save_colors']
        )
        
        logging.info(f"Low-poly model exported to: {model_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting low-poly model: {str(e)}")
        return False

def export_lopoly_report(lopoly_chunk, model_id, base_output_dir):
    """
    Export low-poly processing report.
    
    Args:
        lopoly_chunk (Metashape.Chunk): The low-poly chunk
        model_id (str): Clean model ID
        base_output_dir (str): Base output directory
        
    Returns:
        bool: True if successful
    """
    try:
        paths = get_export_paths(model_id, base_output_dir)
        report_dir = paths['report']['dir']
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"{model_id}_lopoly.pdf")
        
        lopoly_chunk.exportReport(
            path=report_path,
            title=f"{model_id} - Low Poly",
            description=f"Decimated model export for {model_id}",
            page_numbers=True,
            include_system_info=True
        )
        
        logging.info(f"Low-poly report exported to: {report_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error exporting low-poly report: {str(e)}")
        return False

def build_and_export_orthomosaics(chunk, model_id, base_output_dir, config):
    """
    Build orthomosaic and export both full and tiled versions.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        model_id (str): Clean model ID
        base_output_dir (str): Base output directory
        config (dict): Orthomosaic configuration
        
    Returns:
        bool: True if successful
    """
    try:
        ortho_config = config['orthomosaic']
        
        if not chunk.orthomosaic:
            logging.info("Building orthomosaic...")
            
            enable_ortho_gpu = config.get("enable_orthomosaic_gpu", True)
            
            # Save current GPU state before any changes
            saved_gpu_mask = Metashape.app.gpu_mask
            saved_cpu_enable = Metashape.app.cpu_enable
            
            if enable_ortho_gpu:
                # Actually enable GPU for orthomosaic
                gpu_devices = Metashape.app.enumGPUDevices()
                if gpu_devices:
                    Metashape.app.gpu_mask = (1 << len(gpu_devices)) - 1
                    Metashape.app.cpu_enable = False
                    logging.info(f"GPU enabled for orthomosaic: mask={Metashape.app.gpu_mask}, {len(gpu_devices)} device(s)")
                else:
                    logging.warning("No GPU devices found, using CPU for orthomosaic")
                    Metashape.app.cpu_enable = True
            else:
                # Disable GPU for orthomosaic
                Metashape.app.gpu_mask = 0
                Metashape.app.cpu_enable = True
                logging.info("GPU disabled for orthomosaic generation (using CPU only)")
            
            # Build orthomosaic with all parameters from config
            chunk.buildOrthomosaic(
                surface_data=Metashape.DataSource.ModelData,
                blending_mode=getattr(Metashape.BlendingMode, ortho_config['blending_mode']),
                fill_holes=ortho_config.get('fill_holes', True),
                resolution=ortho_config.get('resolution', 0),  # 0 = native resolution
                ghosting_filter=ortho_config.get('ghosting_filter', False),
                cull_faces=ortho_config.get('cull_faces', False),
                refine_seamlines=ortho_config.get('refine_seamlines', False),
                subdivide_task=ortho_config.get('subdivide_task', True),
                workitem_size_cameras=ortho_config.get('workitem_size_cameras', 20),
                workitem_size_tiles=ortho_config.get('workitem_size_tiles', 10),
                max_workgroup_size=ortho_config.get('max_workgroup_size', 100)
            )
            
            # Restore GPU state after orthomosaic generation
            Metashape.app.gpu_mask = saved_gpu_mask
            Metashape.app.cpu_enable = saved_cpu_enable
            logging.info("GPU state restored after orthomosaic generation")
        
        paths = get_export_paths(model_id, base_output_dir)
        ortho_dir = paths['orthomosaic']['dir']
        os.makedirs(ortho_dir, exist_ok=True)
        
        compression = Metashape.ImageCompression()
        compression.tiff_tiled = True
        compression.tiff_overviews = True
        
        compression_type = ortho_config.get("compression", "LZW")
        if compression_type == "LZW":
            compression.tiff_compression = Metashape.ImageCompression.TiffCompressionLZW
        elif compression_type == "JPEG":
            compression.tiff_compression = Metashape.ImageCompression.TiffCompressionJPEG
        elif compression_type == "Packbits":
            compression.tiff_compression = Metashape.ImageCompression.TiffCompressionPackbits
        else:
            compression.tiff_compression = Metashape.ImageCompression.TiffCompressionNone
        
        # Use resolution from config (0 = native resolution)
        resolution = ortho_config.get('export_resolution', 0)
        
        # Get actual resolution from built orthomosaic for tile calculation
        # When resolution=0 was used in buildOrthomosaic, we need the actual value
        actual_resolution = chunk.orthomosaic.resolution if chunk.orthomosaic else 0.001
        resolution_display = "native" if resolution == 0 else f"{resolution}m/px"
        logging.info(f"Orthomosaic actual resolution: {actual_resolution}m/px")
        
        full_ortho_path = os.path.join(ortho_dir, f"{model_id}_full.tif")
        logging.info(f"Exporting full orthomosaic (resolution: {resolution_display})...")
        
        chunk.exportRaster(
            path=full_ortho_path,
            source_data=Metashape.DataSource.OrthomosaicData,
            image_format=Metashape.ImageFormatTIFF,
            image_compression=compression,
            resolution=resolution,  # 0 = native resolution
            save_world=ortho_config.get('save_world', True),
            save_alpha=ortho_config.get('save_alpha', True),
            split_in_blocks=False,
            white_background=True
        )
        logging.info(f"Full orthomosaic exported to: {full_ortho_path}")
        
        # Calculate tile size in pixels using actual orthomosaic resolution
        tile_size_meters = config.get('ortho_tile_size', 0.5)
        tile_size_pixels = int(tile_size_meters / actual_resolution)
        
        tiled_ortho_path = os.path.join(ortho_dir, f"{model_id}.tif")
        logging.info(f"Exporting tiled orthomosaic ({tile_size_meters}m = {tile_size_pixels}px tiles)...")
        
        chunk.exportRaster(
            path=tiled_ortho_path,
            source_data=Metashape.DataSource.OrthomosaicData,
            image_format=Metashape.ImageFormatTIFF,
            image_compression=compression,
            resolution=resolution,  # 0 = native resolution
            save_world=ortho_config.get('save_world', True),
            save_alpha=ortho_config.get('save_alpha', True),
            split_in_blocks=True,
            block_width=tile_size_pixels,
            block_height=tile_size_pixels,
            white_background=True
        )
        logging.info(f"Tiled orthomosaic exported to: {ortho_dir}/")
        
        return True
        
    except Exception as e:
        logging.error(f"Error building/exporting orthomosaics: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def process_chunk(chunk, doc, base_output_dir, config):
    """
    Process a single chunk for dual model export.
    
    Args:
        chunk (Metashape.Chunk): The chunk to process
        doc (Metashape.Document): The document containing the chunk
        base_output_dir (str): Base output directory
        config (dict): Processing configuration
        
    Returns:
        bool: True if successful
    """
    model_id = clean_model_id(chunk.label)
    start_time = time.time()
    
    status = get_transect_status(chunk.label)
    scale_status = status.get("Scale", "")
    
    if scale_status != "PASS":
        logging.info(f"Chunk {model_id} has Scale={scale_status}, skipping (need Scale=PASS)")
        return False
    
    if scale_status == "DONE":
        logging.info(f"Chunk {model_id} already processed (Scale=DONE), skipping...")
        return True
    
    logging.info(f"\n{'='*60}")
    logging.info(f"Processing chunk: {model_id}")
    logging.info(f"{'='*60}")
    
    # Step 1-2: Export hi-poly model and report
    export_hipoly_model(chunk, model_id, base_output_dir, config)
    export_hipoly_report(chunk, model_id, base_output_dir)
    
    # Step 3-7: Create lo-poly chunk (decimation, texture)
    lopoly_chunk, cameras_removed = create_lopoly_chunk(chunk, config)
    
    if lopoly_chunk:
        # Step 8-9: Export lo-poly model and report
        export_lopoly_model(lopoly_chunk, model_id, base_output_dir, config)
        export_lopoly_report(lopoly_chunk, model_id, base_output_dir)
        logging.info("Low-poly chunk exported successfully")
        
        # Step 10: Build orthomosaic from LO-POLY chunk (has reduced cameras)
        build_and_export_orthomosaics(lopoly_chunk, model_id, base_output_dir, config)
    else:
        cameras_removed = 0
        logging.warning("Failed to create low-poly chunk, skipping orthomosaic")
    
    # Step 11: Save PSX with ONLY hi-poly and lo-poly chunks for this model
    output_psx_dir = os.path.join(base_output_dir, "output", "psx")
    os.makedirs(output_psx_dir, exist_ok=True)
    output_psx_path = os.path.join(output_psx_dir, f"{model_id}.psx")
    
    # Filter to only save chunks belonging to this model_id
    chunks_to_save = [c for c in doc.chunks 
                      if c.label == chunk.label or c.label == f"{chunk.label}_lopoly"]
    
    logging.info(f"Saving PSX with {len(chunks_to_save)} chunks (hi-poly + lo-poly) to: {output_psx_path}")
    doc.save(output_psx_path, chunks=chunks_to_save)
    
    # Step 12: Move frames from processing/frames/ to output/frames/
    source_frames = os.path.join(DIRECTORIES["frames"], chunk.label)
    dest_frames = os.path.join(DIRECTORIES["frames_output"], model_id)
    
    frames_moved = False
    if os.path.exists(source_frames):
        try:
            # Create parent directory if needed
            os.makedirs(os.path.dirname(dest_frames), exist_ok=True)
            # Move frames atomically
            shutil.move(source_frames, dest_frames)
            logging.info(f"Moved frames: {source_frames} -> {dest_frames}")
            frames_moved = True
        except Exception as e:
            logging.error(f"Error moving frames: {str(e)}")
            # Don't fail the entire process if frame move fails
    else:
        logging.warning(f"Source frames directory not found: {source_frames}")
    
    # Step 13: Update camera photo paths in PSX to point to new frame locations
    if frames_moved:
        try:
            logging.info("Updating camera photo paths in PSX file...")
            # Reload the PSX we just saved
            temp_doc = Metashape.Document()
            temp_doc.open(output_psx_path, read_only=False)
            
            # Calculate relative path from PSX location to frames
            # PSX is in: output/psx/{model_id}.psx
            # Frames are in: output/frames/{model_id}/
            # Relative path: ../frames/{model_id}/
            relative_frames_dir = os.path.join("..", "frames", model_id)
            
            paths_updated = 0
            # For each chunk in the document (hipoly and lopoly)
            for temp_chunk in temp_doc.chunks:
                # Update each camera's photo path
                for camera in temp_chunk.cameras:
                    if camera.photo and camera.photo.path:
                        # Get filename from old path
                        photo_filename = os.path.basename(camera.photo.path)
                        # Construct new RELATIVE path
                        new_photo_path = os.path.join(relative_frames_dir, photo_filename)
                        # Update the path using Metashape API
                        camera.photo.open(new_photo_path)
                        paths_updated += 1
            
            # Save updated PSX
            temp_doc.save()
            logging.info(f"Updated {paths_updated} camera photo paths to relative paths")
            
        except Exception as e:
            logging.error(f"Error updating PSX photo paths: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the entire process if path update fails
    
    processing_time = time.time() - start_time
    
    update_tracking(chunk.label, {
        "Scale": "DONE",
        "Cameras Removed": str(cameras_removed),
        "Step 3 complete": "True",
        "Step 3 processing time": f"{processing_time:.2f}"
    })
    
    logging.info(f"Completed processing for {model_id} in {processing_time:.2f}s")
    return True

def main():
    """Main function to process dual exports for all Scale=PASS models."""
    project_dir = DIRECTORIES["base"]
    psxraw_dir = DIRECTORIES["psxraw"]
    
    if not os.path.exists(psxraw_dir):
        logging.error(f"PSX raw directory not found: {psxraw_dir}")
        return
    
    tracking_files = get_tracking_files()
    
    if not tracking_files:
        logging.error("No tracking files found. Run step1.py and step2.py first.")
        return
    
    config = PARAMS['processing']['model_processing']
    
    psx_files = [f for f in os.listdir(psxraw_dir) if f.endswith('.psx')]
    
    if not psx_files:
        logging.error(f"No PSX files found in {psxraw_dir}")
        return
    
    logging.info(f"Found {len(psx_files)} PSX files to process")
    
    processed_count = 0
    skipped_count = 0
    
    for psx_file in psx_files:
        psx_path = os.path.join(psxraw_dir, psx_file)
        logging.info(f"\nProcessing PSX file: {psx_file}")
        
        doc = Metashape.Document()
        doc.open(psx_path, read_only=False)
        
        for chunk in doc.chunks:
            try:
                if process_chunk(chunk, doc, project_dir, config):
                    processed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logging.error(f"Error processing chunk {chunk.label}: {str(e)}")
                import traceback
                traceback.print_exc()
                skipped_count += 1
        
        doc.save()
        logging.info(f"Saved {psx_file}")
    
    logging.info(f"\nStep 3 completed: {processed_count} chunks processed, {skipped_count} skipped")

if __name__ == "__main__":
    main()
