import os
import time
from pathlib import Path
import bpy
from mathutils import Vector
import render_config as cfg

def setup_gpu_rendering():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'

    prefs = bpy.context.preferences
    cycles_addon = prefs.addons.get('cycles')
    if cycles_addon is None:
        raise RuntimeError("Cycles add-on is not enabled")

    cycles_prefs = cycles_addon.preferences
    cycles_prefs.get_devices()
    time.sleep(1)

    for i, device in enumerate(cycles_prefs.devices):
        device.use = (i == cfg.gpu_id)
        print(f"{'Enabled' if device.use else 'Disabled'} GPU: {device.name}")

    cycles_prefs.compute_device_type = 'CUDA'


def clear_scene_objs():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.ops.object.delete()


def import_obj(obj_path):
    bpy.ops.wm.obj_import(filepath=obj_path)
    imported = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not imported:
        raise RuntimeError(f"OBJ import failed or produced no mesh: {obj_path}")
    return imported[0]


def center_object_at_world_origin(obj, empty_name=None):
    # Put the mesh origin at its bounding-box center, then move that origin to (0, 0, 0).
    empty_name = cfg.empty_name if empty_name is None else empty_name
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = Vector((0.0, 0.0, 0.0))
    bpy.context.view_layer.update()

    empty = bpy.data.objects.get(empty_name)
    if empty is not None:
        empty.location = Vector((0.0, 0.0, 0.0))


def find_json_folders(root_dir):
    """Find texture folders by locating metadata.json files below the root."""
    renders_list = []
    root_dir = Path(root_dir)
    for metadata_file in root_dir.glob("**/metadata.json"):
        parent_dir = os.path.join(root_dir, str(metadata_file.parent))
        renders_list.append({
            "path": str(metadata_file),
            "parent_dir": parent_dir,
        })
    return renders_list


def setup_render_settings():
    scene = bpy.context.scene
    scene.render.resolution_x = cfg.resolution[0]
    scene.render.resolution_y = cfg.resolution[1]
    scene.render.image_settings.file_format = cfg.file_format

    scene.view_layers["ViewLayer"].use_pass_z = True
    scene.render.film_transparent = True

    # Keep direct highlights intact while reducing indirect-firefly noise.
    scene.cycles.sample_clamp_indirect = 1.0
    scene.cycles.sample_clamp_direct = 0.0
    scene.cycles.blur_glossy = 1.0
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'

    print("Render settings updated: denoising enabled, indirect clamp set to 1.0")


def create_ground_plane(obj):
    """Return the mesh bottom height without creating a visible plane."""
    min_z = min([(obj.matrix_world @ v.co).z for v in obj.data.vertices])
    ground_z = min_z - 0.01
    return ground_z


def setup_depth_output_nodes(scene, output_path, camera_name, angle_deg):
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    render_layers = tree.nodes.new(type="CompositorNodeRLayers")

    # Normalize depth for PNG output.
    normalize_node = tree.nodes.new(type="CompositorNodeNormalize")
    tree.links.new(render_layers.outputs["Depth"], normalize_node.inputs[0])

    depth_output_node = tree.nodes.new(type="CompositorNodeOutputFile")
    depth_output_node.label = "Depth Output"
    depth_output_node.base_path = output_path
    depth_output_node.file_slots[0].path = f"{camera_name}_theta{angle_deg:03d}_depth"
    depth_output_node.format.file_format = 'PNG'
    depth_output_node.format.color_depth = '16'
    depth_output_node.format.color_mode = 'BW'
    tree.links.new(normalize_node.outputs[0], depth_output_node.inputs[0])

    # Use the alpha channel as the object mask.
    mask_output_node = tree.nodes.new(type="CompositorNodeOutputFile")
    mask_output_node.label = "Mask Output"
    mask_output_node.base_path = output_path
    mask_output_node.file_slots[0].path = f"{camera_name}_theta{angle_deg:03d}_mask"
    mask_output_node.format.file_format = 'PNG'
    mask_output_node.format.color_mode = 'BW'
    mask_output_node.format.color_depth = '8'
    # This requires transparent film to be enabled in render settings.
    tree.links.new(render_layers.outputs["Alpha"], mask_output_node.inputs[0])

    print("Compositor node tree updated: depth and mask outputs enabled")


def set_background():
    # Ensure the scene has a world environment.
    if not bpy.context.scene.world:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    world = bpy.context.scene.world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Replace existing world nodes with a simple background.
    nodes.clear()

    background_node = nodes.new(type='ShaderNodeBackground')
    background_node.inputs['Color'].default_value = (1, 1, 1, 1)
    background_node.inputs['Strength'].default_value = cfg.world_strength

    output_node = nodes.new(type='ShaderNodeOutputWorld')

    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

    print("World background configured.")
