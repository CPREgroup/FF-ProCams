# FF-ProCams

This repository contains tools for synthetic dataset generation using Blender and projector-camera rendering.

## Synthetic Dataset Generation

The `synthetic_dataset_generation` folder provides a Blender-based pipeline for generating multi-view synthetic data with projected patterns.

The pipeline renders textured 3D objects from multiple viewpoints and saves RGB images, depth maps, masks, and camera/projector pose metadata.

## Folder Structure

```text
synthetic_dataset_generation/
  controller_kill_after_time.py
  render_batch_both_8view_multiproj.py
  render_config.py
  blender_scene.py
  orbit_renderer.py
  materials.py
  projector_patterns.py
