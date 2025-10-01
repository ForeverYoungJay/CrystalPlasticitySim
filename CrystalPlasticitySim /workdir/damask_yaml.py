import damask
import json
import os

def update_load_yaml(json_input: str) -> str:
    """
    Update the deformation gradient tensor in a load YAML file and save it in the same folder.
    
    Takes a JSON input with the following keys:
        - load_file: Name of the original load YAML file.
        - new_F12: New value for F12.
        - new_F13: New value for F13.
        - new_F23: New value for F23.
    
    Returns:
        Absolute path of the updated YAML file.
    """
    try:
        # Parse JSON input
        params = json.loads(json_input)
        yaml_file = params["load_file"]
        new_F12 = params["new_F12"]
        new_F13 = params["new_F13"]
        new_F23 = params["new_F23"]

        # Load the YAML file
        config = damask.YAML.load(yaml_file)

        # Update the deformation gradient values
        for loadstep in config['loadstep']:
            dot_F = loadstep['boundary_conditions']['mechanical']['dot_F']
            dot_F[0][1] = new_F12
            dot_F[0][2] = new_F13
            dot_F[1][2] = new_F23

        # Get the absolute directory of the original YAML file
        yaml_dir = os.path.dirname(os.path.abspath(yaml_file))

        # Generate the updated file name
        updated_filename = (
            f"load_F12_{new_F12:.6e}_F13_{new_F13:.6e}_F23_{new_F23:.6e}.yaml"
        )

        # Absolute path of the new YAML file
        updated_filepath = os.path.join(yaml_dir, updated_filename)

        # Save the updated YAML file in the same directory as the original
        config.save(updated_filepath)

        return updated_filepath  # Return the absolute path of the updated YAML file

    except KeyError as e:
        return f"Missing required key in JSON input: {e}"
    except Exception as e:
        return f"An error occurred: {e}"


def update_material_properties(file_path, new_values):
    """
    Update specified material properties in a DAMASK material configuration file.

    Parameters:
    - file_path (str): Path to the existing material configuration file.
    - new_values (dict): Dictionary containing property names as keys and their new values as values.
      Expected keys and their corresponding value types are:
        - 'xi_0_sl' (integer): Initial critical shear stress for slip, in MPa.
        - 'xi_inf_sl' (integer): Maximum critical shear stress for slip, in MPa.
        - 'h_0_sl-sl' (integer): Initial hardening modulus for slip-slip interactions, in MPa.

    Returns:
    - str: Path to the newly created updated material configuration file.
    """
    # Load the existing material configuration
    material_config = damask.ConfigMaterial.load(file_path)

    # Navigate to the 'plastic' properties of the 'Ni3Al' phase
    try:
        plastic_props = material_config['phase']['Ni3Al']['mechanical']['plastic']
    except KeyError as e:
        raise KeyError(f"Missing expected key in material configuration: {e}")

    # Update the specified properties
    for key, value in new_values.items():
        if key in plastic_props:
            # Convert MPa to Pascals (for DAMASK format)
            plastic_props[key] = [value * 1e6]  
        else:
            raise KeyError(f"Property '{key}' not found in the 'plastic' section.")

    # Map full keys to short labels for filename
    label_map = {
        'xi_0_sl': 'xi0',
        'xi_inf_sl': 'xiInf',
        'h_0_sl-sl': 'h0'
    }
    short_labels = [f"{label_map[key]}{int(value)}" for key, value in new_values.items()]
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    new_file_name = f"{base_name}_" + "_".join(short_labels) + ".yaml"

    output_path = os.path.join(os.path.dirname(file_path), new_file_name)
    material_config.save(output_path)

    return output_path


