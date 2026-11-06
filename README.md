<!-- <p align="center">
  <img src="assets/teaser.png" width="800">
</p> -->

# FF-ProCams: Feed-Forward Gaussian Splatting for Projector-Camera System

FF-ProCams is a feed-forward Gaussian splatting framework for projector-camera systems. 
- This repository currently releases theBlender-based synthetic data generation pipeline used by FF-ProCams.
- The training code, pretrained models, and dataset links will be released in future updates.

## Qualitative Results

<p align="center">
  <img src="assets/qualitative_results.png" width="100%">
</p>

The figure presents additional qualitative results across diverse
geometries and materials, including ground-truth images, rendered views,
albedo, and roughness.

## Status

- Synthetic dataset generation scripts: released
- FF-ProCams training code: coming soon
- Evaluation scripts: coming soon
- Pretrained models: coming soon
- Dataset download links: coming soon

## Roadmap

- [x] Release synthetic dataset generation pipeline
- [ ] Add example Blender scene and sample assets
- [ ] Add example generated data structure
- [ ] Release FF-ProCams training code
- [ ] Release pretrained models
- [ ] Release dataset download links

## Synthetic Dataset Generation

The `synthetic_dataset_generation` folder provides scripts for generating synthetic datasets using Blender and projector-camera rendering.

The pipeline renders textured 3D objects from multiple viewpoints under projected patterns. It saves RGB images, depth maps, object masks, and camera/projector pose metadata for each generated scene.

## Folder Structure

```text
synthetic_dataset_generation/
  controller_kill_after_time.py
  render_batch_both_8view_multiproj.py
  render_config.py
  render_defaults.yaml
  blender_scene.py
  orbit_renderer.py
  materials.py
  projector_patterns.py
```

## Requirements

- Blender 4.x
- Python 3

## Usage

Run the controller script from the repository root:

```bash
python synthetic_dataset_generation/controller_kill_after_time.py --start 0 --end 1
```

The controller launches Blender in background mode and runs the rendering pipeline.

The `--start` and `--end` arguments select a range of texture folders to process. This is useful for splitting dataset generation across multiple machines or GPUs.

## Output

For each texture folder and object, the pipeline creates an output folder containing rendered images and metadata.

Example output structure:

```text
textures/
  material_xxx/
    object_name/
      path_0_theta000_pattern.png
      path_0_theta000_depth.png
      path_0_theta000_mask.png
      render_poses.json
```

The generated metadata file `render_poses.json` contains camera and projector pose information for each rendered view.

## Citation

Citation information will be added after release.

## License

License information will be added before public release.
