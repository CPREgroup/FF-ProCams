import ast
import math
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().with_name("render_defaults.yaml")


def _parse_yaml_value(raw_value):
    value = raw_value.strip()
    lower_value = value.lower()
    if lower_value == "true":
        return True
    if lower_value == "false":
        return False
    if lower_value in {"none", "null"}:
        return None
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("\"'")


def _load_defaults(path):
    defaults = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, raw_value = line.split(":", 1)
            defaults[key.strip()] = _parse_yaml_value(raw_value)
    return defaults


_DEFAULTS = _load_defaults(CONFIG_PATH)


def get_default(key):
    return _DEFAULTS[key]

# Mutable runtime values used by the rendering modules. Keep these names stable.
resolution = tuple(_DEFAULTS["resolution"])
file_format = _DEFAULTS["file_format"]
empty_name = _DEFAULTS["orbit_center_name"]
cameras_to_render = list(_DEFAULTS["camera_names"])
min_height_above_ground = _DEFAULTS["min_camera_height_above_ground"]
num_orbit_views = _DEFAULTS["orbit_view_count"]
camera_phi_radians = math.radians(_DEFAULTS["camera_polar_angle_degrees"])
projector_phi_radians = math.radians(_DEFAULTS["projector_polar_angle_degrees"])
projector_distance_ratio = _DEFAULTS["projector_distance_ratio"]
projector_name = _DEFAULTS["projector_camera_name"]
projector_light_name = _DEFAULTS["projector_light_name"]
projector_energy = _DEFAULTS["projector_energy"]
world_strength = _DEFAULTS["world_strength"]
pattern_dir = _DEFAULTS["pattern_dir"]
pattern_width, pattern_height = _DEFAULTS["pattern_size"]
samples = _DEFAULTS["samples"]
radius = _DEFAULTS["camera_radius"]
start_idx = _DEFAULTS["start_index"]
end_idx = _DEFAULTS["end_index"]
gpu_id = _DEFAULTS["gpu_id"]
expected_file_count = _DEFAULTS["expected_file_count"]
folder_total = _DEFAULTS["folder_total"]
camera_light_name = _DEFAULTS["camera_light_name"]
camera_light_energy = _DEFAULTS["camera_light_energy"]
use_camera_light = _DEFAULTS["use_camera_light"]
obj_folder = None
textures_root = None


def _parse_bool(value):
    return value.lower() in {"1", "true", "yes", "on"}


def _parse_resolution(value):
    width, height = value.lower().replace("*", "x").split("x", 1)
    return int(width), int(height)


def parse_blender_args(argv=None):
    """Parse arguments forwarded by Blender after "--" and update this module."""
    global obj_folder, textures_root, pattern_dir, samples, radius, start_idx, end_idx
    global gpu_id, resolution, file_format, num_orbit_views, camera_phi_radians
    global projector_phi_radians, projector_distance_ratio, projector_energy
    global world_strength, pattern_width, pattern_height, expected_file_count
    global folder_total, camera_light_energy, use_camera_light

    argv = sys.argv if argv is None else argv
    if "--" in argv:
        idx = argv.index("--")
        args = argv[idx + 1:]
        for arg in args:
            if arg.startswith("--obj_folder="):
                obj_folder = arg.split("=", 1)[1]
            elif arg.startswith("--textures_root="):
                textures_root = arg.split("=", 1)[1]
            elif arg.startswith("--pattern_dir="):
                pattern_dir = arg.split("=", 1)[1]
            elif arg.startswith("--samples="):
                samples = int(arg.split("=", 1)[1])
            elif arg.startswith("--radius="):
                radius = float(arg.split("=", 1)[1])
            elif arg.startswith("--start="):
                start_idx = int(arg.split("=", 1)[1])
            elif arg.startswith("--end="):
                end_idx = int(arg.split("=", 1)[1])
            elif arg.startswith("--gpu_id="):
                gpu_id = int(arg.split("=", 1)[1])
            elif arg.startswith("--resolution="):
                resolution = _parse_resolution(arg.split("=", 1)[1])
            elif arg.startswith("--file_format="):
                file_format = arg.split("=", 1)[1]
            elif arg.startswith("--num_orbit_views="):
                num_orbit_views = int(arg.split("=", 1)[1])
            elif arg.startswith("--camera_phi_deg="):
                camera_phi_radians = math.radians(float(arg.split("=", 1)[1]))
            elif arg.startswith("--projector_phi_deg="):
                projector_phi_radians = math.radians(float(arg.split("=", 1)[1]))
            elif arg.startswith("--projector_distance_ratio="):
                projector_distance_ratio = float(arg.split("=", 1)[1])
            elif arg.startswith("--projector_energy="):
                projector_energy = float(arg.split("=", 1)[1])
            elif arg.startswith("--world_strength="):
                world_strength = float(arg.split("=", 1)[1])
            elif arg.startswith("--pattern_width="):
                pattern_width = int(arg.split("=", 1)[1])
            elif arg.startswith("--pattern_height="):
                pattern_height = int(arg.split("=", 1)[1])
            elif arg.startswith("--expected_file_count="):
                expected_file_count = int(arg.split("=", 1)[1])
            elif arg.startswith("--folder_total="):
                folder_total = int(arg.split("=", 1)[1])
            elif arg.startswith("--camera_light_energy="):
                camera_light_energy = float(arg.split("=", 1)[1])
            elif arg.startswith("--use_camera_light="):
                use_camera_light = _parse_bool(arg.split("=", 1)[1])

    if obj_folder is None or textures_root is None:
        raise RuntimeError("Both --obj_folder and --textures_root must be provided.")

    print(
        f"Parsed arguments: obj_folder={obj_folder}, textures_root={textures_root}, "
        f"pattern_dir={pattern_dir}, samples={samples}, radius={radius}, "
        f"start_idx={start_idx}, end_idx={end_idx}, resolution={resolution}"
    )
