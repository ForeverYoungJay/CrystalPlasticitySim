import numpy as np
import damask
import json

def calculate_deviation_angle(json_input: str) -> dict:
    """
    Calculate the deviation angle between simulated and experimental orientations.
    Requires a JSON input containing:
        - simulated_file: Name of the result file.
        - experimental_quaternion: A list representing the experimental quaternion [w, x, y, z].
    Returns a dictionary with the deviation angle (degrees) and simulated quaternion.
    """
    try:
        # Parse JSON input
        params = json.loads(json_input)
        simulated_file = params["simulated_file"]
        experimental_quaternion = params["experimental_quaternion"]

        # Load results from the simulated file
        r = damask.Result(simulated_file)
        r_last = r.view(increments=-1)
        quaternion_simulated = r_last.get('O')[0]  # Extract the last quaternion orientation

        # Convert quaternions to rotation matrices
        R_simulated = quaternion_to_rotation_matrix(quaternion_simulated)
        R_experimental = quaternion_to_rotation_matrix(experimental_quaternion)

        # Compute the deviation angle
        deviation_angle = deviation_angle_between_rotations(R_simulated, R_experimental)

        return {
            "deviation_angle": deviation_angle,
            "simulated_quaternion": quaternion_simulated
        }
    except KeyError as e:
        return {"error": f"Missing required key in JSON input: {e}"}
    except Exception as e:
        return {"error": str(e)}

def quaternion_to_rotation_matrix(q: list) -> np.ndarray:
    """
    Convert a quaternion to a 3x3 rotation matrix.
    """
    w, x, y, z = q
    R = np.array([
        [1 - 2 * (y**2 + z**2), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x**2 + z**2), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x**2 + y**2)]
    ])
    return R

def deviation_angle_between_rotations(R1: np.ndarray, R2: np.ndarray) -> float:
    """
    Compute the deviation angle between two rotation matrices.
    """
    R_relative = np.dot(R1.T, R2)
    trace = np.trace(R_relative)
    
    # Ensure the trace is within the valid range for arccos
    trace = max(min(trace, 3), -1)

    # Compute the deviation angle
    angle = np.arccos((trace - 1) / 2)
    return np.degrees(angle)


def read_experimental_data(file_path):
        data = np.loadtxt(file_path, skiprows=1)
        true_strain = data[:, 1] 
        true_stress = data[:, 0]
        return true_strain, true_stress


def extract_simulation_results(hdf5_file):
    r = damask.Result(hdf5_file)
    try:
        r.add_stress_Cauchy(P='P', F='F')
        r.add_strain(F='F', t='V', m=0.0)
    except Exception as e:
        print(f"stress and strain is exist in the file")
    # Extract the true strain and stress values

    strain_xx = []
    stress_xx = []

    for increment in r.increments:
        r_view = r.view(increments=[increment])
        true_strain = r_view.get('epsilon_V^0.0(F)')
        true_stress = r_view.get('sigma')
        
        if true_strain is None or true_stress is None:
            print(f"Missing data in increment {increment}")
            continue
        
        strain_xx.append(np.mean(true_strain[..., 0, 0]))
        stress_xx.append(np.mean(true_stress[..., 0, 0]))

    if not strain_xx or not stress_xx:
        raise ValueError("No valid strain or stress data extracted.")

    return np.array(strain_xx), np.array(stress_xx)