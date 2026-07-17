import glob
import json
import math
import os
import bpy
from mathutils import Vector

import render_config as cfg
from blender_scene import setup_depth_output_nodes
from projector_patterns import (
    list_projector_patterns,
    pattern_name_from_path,
    switch_projector_image,
)


def _rigidize_matrix_world(mat):
    loc, rot, _scale = mat.decompose()
    rigid = rot.to_matrix().to_4x4()
    rigid.translation = loc
    return rigid


def _camera_intrinsics(camera, scene):
    render_width = scene.render.resolution_x * scene.render.resolution_percentage / 100
    render_height = scene.render.resolution_y * scene.render.resolution_percentage / 100

    camd = camera.data
    aspect = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

    sensor_fit = camd.sensor_fit
    if sensor_fit == 'AUTO':
        sensor_fit = 'HORIZONTAL' if (render_width * scene.render.pixel_aspect_x) >= (render_height * scene.render.pixel_aspect_y) else 'VERTICAL'

    if sensor_fit == 'HORIZONTAL':
        s_u = render_width / camd.sensor_width
        s_v = render_height * aspect / camd.sensor_width
    else:
        s_u = render_width / (camd.sensor_height / aspect)
        s_v = render_height / camd.sensor_height

    return {
        "h": render_height,
        "w": render_width,
        "fx": camd.lens * s_u,
        "fy": camd.lens * s_v,
        "cx": render_width / 2.0,
        "cy": render_height / 2.0,
    }


def _projector_intrinsics(projector, scene):
    pattern_w, pattern_h = cfg.pattern_width, cfg.pattern_height
    proj = projector.data
    aspect = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    scale_world = projector.matrix_world.to_scale()
    proj_scale_y_over_z = abs(scale_world.y) / abs(scale_world.z)
    print("scale_world:", scale_world, proj_scale_y_over_z)

    sensor_fit = proj.sensor_fit
    if sensor_fit == 'AUTO':
        sensor_fit = 'HORIZONTAL' if (pattern_w * scene.render.pixel_aspect_x) >= (pattern_w * scene.render.pixel_aspect_y) else 'VERTICAL'

    if sensor_fit == 'HORIZONTAL':
        s_u = pattern_w / proj.sensor_width
        s_v = pattern_h * aspect / proj.sensor_width
    else:
        s_u = pattern_w / (proj.sensor_height / aspect)
        s_v = pattern_h / proj.sensor_height

    return {
        "proj_fx": proj.lens * s_u,
        "proj_fy": proj.lens * s_v * proj_scale_y_over_z,
        "proj_cx": pattern_w / 2,
        "proj_cy": pattern_h / 2,
    }


def _rename_depth_mask_outputs(output_path, camera_name, road, angle_deg):
    expected_name_depth = f"path_{road}_theta{angle_deg:03d}_depth.png"
    actual_files_depth = glob.glob(
        os.path.join(output_path, f"{camera_name}_theta{angle_deg:03d}_depth*.png")
    )
    expected_name_mask = f"path_{road}_theta{angle_deg:03d}_mask.png"
    actual_files_mask = glob.glob(
        os.path.join(output_path, f"{camera_name}_theta{angle_deg:03d}_mask*.png")
    )

    if actual_files_depth:
        latest_file_depth = max(actual_files_depth, key=os.path.getctime)
        os.rename(latest_file_depth, os.path.join(output_path, expected_name_depth))
        print(f"Renamed depth map: {os.path.basename(latest_file_depth)} -> {expected_name_depth}")

    if actual_files_mask:
        latest_file_mask = max(actual_files_mask, key=os.path.getctime)
        os.rename(latest_file_mask, os.path.join(output_path, expected_name_mask))
        print(f"Renamed mask: {os.path.basename(latest_file_mask)} -> {expected_name_mask}")


def _metadata_image_path(output_path, filename):
    deal_path = output_path
    parts = deal_path.strip(os.sep).split(os.sep)
    last_four = parts[-4:]
    file_path = os.path.join(*last_four)
    return os.path.join("/", file_path, filename)


def render_angle_steps(output_path, obj_name, ground_z):
    """Render all configured camera views and projector patterns for one mesh."""

    scene = bpy.context.scene
    empty = bpy.data.objects.get(cfg.empty_name)
    if empty is None:
        raise RuntimeError(f"Orbit center object not found: {cfg.empty_name}")

    views = []
    camera_meta = None
    projector_meta = None
    projector = bpy.data.objects.get(cfg.projector_name)
    projector_light = bpy.data.objects.get(cfg.projector_light_name)
    if projector is None:
        raise RuntimeError(f"Projector camera not found: {cfg.projector_name}")
    if projector_light is None:
        raise RuntimeError(f"Projector light not found: {cfg.projector_light_name}")

    for camera_name in cfg.cameras_to_render:
        camera = bpy.data.objects.get(camera_name)
        if camera is None:
            print(f"Camera not found, skipping: {camera_name}")
            continue

        camera_light = bpy.data.objects.get(cfg.camera_light_name)
        if cfg.use_camera_light:
            if camera_light is None:
                raise RuntimeError(f"Camera-aligned light not found: {cfg.camera_light_name}")
            if camera_light.type != "LIGHT":
                raise RuntimeError(f"{cfg.camera_light_name} is not a light object")
            camera_light.data.energy = cfg.camera_light_energy
            camera_light.hide_render = False
            camera_light.hide_viewport = False

        bpy.context.scene.camera = camera
        pattern_files = list_projector_patterns(cfg.pattern_dir)

        theta_camera = [i * (2 * math.pi / cfg.num_orbit_views) for i in range(cfg.num_orbit_views)]

        for road in range(1):
            phi_camera = cfg.camera_phi_radians
            phi_proj = cfg.projector_phi_radians

            for theta in theta_camera:
                # Convert spherical coordinates to Cartesian coordinates.
                camera_x = empty.location.x + cfg.radius * math.sin(phi_camera) * math.cos(theta)
                camera_y = empty.location.y + cfg.radius * math.sin(phi_camera) * math.sin(theta)
                camera_z = empty.location.z + cfg.radius * math.cos(phi_camera)
                camera.location = Vector((camera_x, camera_y, camera_z))

                projector_distance = cfg.radius * cfg.projector_distance_ratio
                projector_x = empty.location.x + projector_distance * math.sin(phi_proj) * math.cos(theta)
                projector_y = empty.location.y + projector_distance * math.sin(phi_proj) * math.sin(theta)
                projector_z = empty.location.z + projector_distance * math.cos(phi_proj)
                projector.location = Vector((projector_x, projector_y, projector_z))

                # Keep the camera aimed at the orbit center.
                direction_cam = empty.location - camera.location
                rot_quat = direction_cam.to_track_quat('-Z', 'Y')
                camera.rotation_euler = rot_quat.to_euler()

                # Keep the projector aimed at the orbit center.
                direction_pro = empty.location - projector.location
                rot_quat = direction_pro.to_track_quat('-Z', 'Y')
                projector.rotation_euler = rot_quat.to_euler()

                bpy.context.view_layer.update()

                c2w_list = [list(row) for row in camera.matrix_world]
                p2w = _rigidize_matrix_world(projector.matrix_world)
                p2w_list = [list(row) for row in p2w]
                angle_deg = int(math.degrees(theta)) % 360
                filename = f"path_{road}_theta{angle_deg:03d}.png"
                filepath = os.path.join(output_path, filename)
                scene.render.filepath = filepath

                print(
                    f"Rendering {filename}; camera=({camera_x:.2f},{camera_y:.2f},{camera_z:.2f}); "
                    f"projector=({projector_x:.2f},{projector_y:.2f},{projector_z:.2f})"
                )

                setup_depth_output_nodes(scene, output_path, camera_name, angle_deg)

                view_id = f"path_{road}_theta{angle_deg:03d}"
                camera_intrinsics = _camera_intrinsics(camera, scene)
                projector_intrinsics = _projector_intrinsics(projector, scene)

                if camera_meta is None:
                    camera_meta = camera_intrinsics

                if projector_meta is None:
                    projector_meta = {
                        "projector_energy": cfg.projector_energy,
                        "proj_lens": projector.data.lens,
                    }

                view_entry = {
                    "view_id": view_id,
                    "c2w": c2w_list,
                    "p2w": p2w_list,
                    **projector_intrinsics,
                    "patterns": [],
                }

                depth_mask_done = False

                for pattern_path in pattern_files:
                    pattern_name = pattern_name_from_path(pattern_path)

                    filename = f"path_{road}_theta{angle_deg:03d}_{pattern_name}.png"
                    filepath = os.path.join(output_path, filename)
                    scene.render.filepath = filepath

                    switch_projector_image("pattern", str(pattern_path))

                    # Depth and mask are identical across patterns for one view.
                    if depth_mask_done:
                        scene.use_nodes = False
                    else:
                        scene.use_nodes = True

                    bpy.ops.render.render(write_still=True)
                    scene.use_nodes = True

                    if not depth_mask_done:
                        _rename_depth_mask_outputs(output_path, camera_name, road, angle_deg)
                        depth_mask_done = True

                    view_entry["patterns"].append({
                        "file_path": _metadata_image_path(output_path, filename),
                        "projector_image": pattern_name,
                    })
                views.append(view_entry)

    json_data = {
        "scene_name": obj_name,
        "camera": camera_meta,
        "projector": projector_meta,
        "views": views,
    }

    json_path = os.path.join(output_path, "render_poses.json")
    print(f"ready save the file to {json_path}")
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=4)

    print(f"Pose metadata saved to {json_path}")
