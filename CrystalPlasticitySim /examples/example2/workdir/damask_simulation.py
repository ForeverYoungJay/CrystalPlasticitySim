import os
import json
from langchain.tools import tool


import os

def run_damask_simulation(load_file: str, grid_file: str, material_file: str) -> str:
    """
    Run the DAMASK simulation using paths to the load file, grid file, and material file.
    The simulation is executed in the same directory as the input files.

    Parameters:
    - load_file (str): Path to the load YAML file.
    - grid_file (str): Path to the grid file.
    - material_file (str): Path to the material file.

    Returns:
    - str: Absolute path to the result HDF5 file, or an error message if the simulation fails.
    """
    try:
        # Resolve absolute paths
        load_file = os.path.abspath(load_file)
        grid_file = os.path.abspath(grid_file)
        material_file = os.path.abspath(material_file)

        # Determine working directory (based on load file location)
        workdir = os.path.dirname(load_file)

        if not os.path.isdir(workdir):
            return f"Error: Work directory {workdir} does not exist."

        # Construct output file name
        result_file = os.path.join(
            workdir,
            f"{os.path.splitext(os.path.basename(grid_file))[0]}_"
            f"{os.path.splitext(os.path.basename(load_file))[0]}_"
            f"{os.path.splitext(os.path.basename(material_file))[0]}.hdf5"
        )


        # Command to run DAMASK 
        command = (
            f"DAMASK_grid --load \"{load_file}\" "
            f"--geom \"{grid_file}\" "
            f"--material \"{material_file}\" "
            f"--workingdirectory \"{workdir}\" > /dev/null 2>&1"
        )

        # Execute command
        exit_code = os.system(command)

        if exit_code != 0:
            raise RuntimeError(f"DAMASK simulation failed with command:\n{command}\nExit code: {exit_code}")

        return os.path.abspath(result_file)

    except Exception as e:
        return f"Error: {str(e)}"


