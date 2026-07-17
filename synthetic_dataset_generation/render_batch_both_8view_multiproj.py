import os
import sys
import time
from pathlib import Path
import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import render_config as cfg
from blender_scene import (
    center_object_at_world_origin,
    clear_scene_objs,
    create_ground_plane,
    find_json_folders,
    import_obj,
    set_background,
    setup_gpu_rendering,
    setup_render_settings,
)
from materials import apply_textures
from orbit_renderer import render_angle_steps


def clear_folder(folder_path):
    folder = Path(folder_path)

    for item in folder.iterdir():
        if item.is_dir():
            item.rmdir()
        else:
            item.unlink()
    print(f"Cleared folder: {folder_path}")


def process_folder(texture_dir, obj_name):
    obj = bpy.context.object
    if obj is None:
        raise Exception("No active object selected.")

    ground_z = create_ground_plane(obj)
    output_base_folder = os.path.join(texture_dir, obj_name)
    texture_folder = output_base_folder
    if not os.path.exists(texture_folder):
        os.makedirs(texture_folder, exist_ok=True)

    if len([f for f in os.listdir(texture_folder)]) != cfg.expected_file_count:
        apply_textures(obj, texture_dir)

        try:
            original_camera = bpy.context.scene.camera
            setup_render_settings()
            print(os.path.exists(texture_folder))
            render_angle_steps(texture_folder, obj_name, ground_z)
            while len([f for f in os.listdir(texture_folder)]) != cfg.expected_file_count:
                clear_folder(texture_folder)
                render_angle_steps(texture_folder, obj_name, ground_z)
            bpy.context.scene.camera = original_camera
        except Exception as e:
            print(f"Error while processing {texture_dir}: {str(e)}")

    print("Processing complete.")


def main():
    cfg.parse_blender_args()

    print(cfg.samples)
    time.sleep(2)
    setup_gpu_rendering()
    set_background()

    renders_folders = find_json_folders(cfg.textures_root)
    renders_folders = renders_folders[cfg.start_idx:cfg.end_idx]
    print(cfg.end_idx)
    print(len(renders_folders))

    obj_files = [f for f in os.listdir(cfg.obj_folder) if f.endswith('.obj')]
    obj_files.sort()

    if renders_folders:
        for renders_info in renders_folders:
            texture_dir = renders_info["parent_dir"]
            total_file_count_par = len([f for f in os.listdir(texture_dir)])
            if total_file_count_par != cfg.folder_total:
                for obj_file in obj_files:
                    obj_name = os.path.basename(obj_file)
                    obj_name = os.path.splitext(obj_name)[0]
                    obj_path = os.path.join(cfg.obj_folder, obj_file)
                    print(f"Processing mesh: {obj_file}")
                    clear_scene_objs()
                    obj = import_obj(obj_path)
                    center_object_at_world_origin(obj, empty_name=cfg.empty_name)
                    process_folder(texture_dir, obj_name)

                print("All meshes processed.")
            else:
                print("Skipping folder because it already has the expected file count.")
    else:
        print(f"No metadata.json files found under {cfg.textures_root}")


if __name__ == "__main__":
    main()
