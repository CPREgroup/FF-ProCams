import os
import bpy

def apply_textures(obj, texture_folder):
    """Apply PBR texture maps from a folder to the active mesh material."""
    if not obj.active_material:
        obj.active_material = bpy.data.materials.new(name="PBR_Material")
    mat = obj.active_material
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Build a minimal Principled BSDF material graph.
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Texture filename keywords mapped to Principled BSDF inputs.
    texture_rules = {
        'basecolor': {'input': 'Base Color', 'space': 'sRGB'},
        'diffuse': {'input': 'Base Color', 'space': 'sRGB'},
        'normal': {'input': 'Normal', 'space': 'Non-Color', 'converter': 'ShaderNodeNormalMap'},
        'roughness': {'input': 'Roughness', 'space': 'Non-Color'},
        'metallic': {'input': 'Metallic', 'space': 'Non-Color'},
        # 'height': {'input': 'Normal', 'space': 'Non-Color', 'converter': 'ShaderNodeBump'}
    }

    # Load and connect all supported texture maps in the folder.
    for tex_file in os.listdir(texture_folder):
        tex_lower = tex_file.lower()
        for key, rule in texture_rules.items():
            if key in tex_lower and tex_lower.endswith(('.png', '.jpg', '.jpeg')):
                tex_path = os.path.join(texture_folder, tex_file)
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.image = bpy.data.images.load(tex_path)
                tex_node.image.colorspace_settings.name = rule['space']

                if 'converter' in rule:
                    converter = nodes.new(rule['converter'])

                    if rule['converter'] == 'ShaderNodeBump':
                        # Bump nodes use the Height input and a modest strength.
                        if principled.inputs['Normal'].is_linked:
                            print(f"Skipping bump map ({tex_file}) because the Normal input is already linked.")
                            # Remove unused nodes to keep the graph clean.
                            nodes.remove(converter)
                            nodes.remove(tex_node)
                            continue

                        converter.inputs['Strength'].default_value = 0.2
                        links.new(tex_node.outputs['Color'], converter.inputs['Height'])
                        links.new(converter.outputs['Normal'], principled.inputs['Normal'])

                    # Normal maps require a Normal Map converter node.
                    elif 'Normal' in rule['converter']:
                        links.new(tex_node.outputs['Color'], converter.inputs['Color'])
                        links.new(converter.outputs['Normal'], principled.inputs['Normal'])

                    else:
                        links.new(tex_node.outputs['Color'], converter.inputs['Color'])
                        if rule['input'] == 'Displacement':
                            links.new(converter.outputs[0], output.inputs['Displacement'])
                        else:
                            links.new(converter.outputs[0], principled.inputs[rule['input']])
                else:
                    if rule['input'] == 'Base Color':
                        sat = nodes.new('ShaderNodeHueSaturation')
                        sat.inputs['Saturation'].default_value = 3.0
                        links.new(tex_node.outputs['Color'], sat.inputs['Color'])
                        links.new(sat.outputs['Color'], principled.inputs['Base Color'])
                    else:
                        links.new(tex_node.outputs['Color'], principled.inputs[rule['input']])

                print(f"Connected texture: {tex_file} -> {rule['input']}")
