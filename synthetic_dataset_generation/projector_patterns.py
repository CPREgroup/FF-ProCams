from pathlib import Path
import bpy

def switch_projector_image(image_datablock_name, new_image_name):
    """Point an existing Blender image datablock at a new projector pattern."""
    img = bpy.data.images.get(image_datablock_name)

    if img:
        img.filepath = new_image_name

        try:
            img.reload()
            print(f"Projector pattern switched to: {new_image_name}")
        except Exception as e:
            print(f"Could not reload image, path may be invalid: {new_image_name} | error: {e}")
    else:
        print(f"Image datablock not found: {image_datablock_name}")


def list_projector_patterns(pattern_dir):
    pattern_dir = Path(pattern_dir)
    if not pattern_dir.is_dir():
        raise RuntimeError(f"Pattern directory does not exist: {pattern_dir}")

    def sort_key(path):
        name = path.stem.lower()
        if name.startswith("lollipop_"):
            return (0, name)
        if name == "all_black":
            return (1, name)
        if name == "all_white":
            return (2, name)
        return (3, name)

    pattern_files = sorted(
        [
            p for p in pattern_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
        ],
        key=sort_key,
    )

    if not pattern_files:
        raise RuntimeError(f"Pattern directory contains no images: {pattern_dir}")

    return pattern_files


def pattern_name_from_path(pattern_path):
    return pattern_path.stem
