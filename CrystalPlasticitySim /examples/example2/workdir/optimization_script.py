import os
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Importing functions from local scripts
from damask_simulation import run_damask_simulation
from damask_results import calculate_deviation_angle
from damask_yaml import update_damask_yaml

# Constants
EXPERIMENTAL_QUATERNION = [0.03451538, 0.56773038, 0.38495706, 0.72684178]
LOAD_FILE = os.path.abspath('workdir/load.yaml')
GRID_FILE = os.path.abspath('workdir/grid.vti')
MATERIAL_FILE = os.path.abspath('workdir/material.yaml')
RESULTS_CSV = os.path.abspath('workdir/optimization_results.csv')

# Optimization bounds
BOUNDS = [(-0.003, 0.003), (-0.003, 0.003), (-0.003, 0.003)]

# Initialize results logging
with open(RESULTS_CSV, 'w') as f:
    f.write('F12,F13,F23,Simulated_Quaternion,Deviation_Angle\n')

# Function to run simulation and calculate deviation angle
def objective_function(F):
    F12, F13, F23 = F
    # Update YAML file with new deformation gradients
    updated_yaml_path = update_damask_yaml(json.dumps({
        'load_file': LOAD_FILE,
        'new_F12': F12,
        'new_F13': F13,
        'new_F23': F23
    }))

    # Run DAMASK simulation
    result_file = run_damask_simulation(json.dumps({
        'load_file': updated_yaml_path,
        'grid_file': GRID_FILE,
        'material_file': MATERIAL_FILE
    }))

    # Calculate deviation angle
    result = calculate_deviation_angle(json.dumps({
        'simulated_file': result_file,
        'experimental_quaternion': EXPERIMENTAL_QUATERNION
    }))

    deviation_angle = result['deviation_angle']
    simulated_quaternion = result['simulated_quaternion']

    # Log results
    with open(RESULTS_CSV, 'a') as f:
        f.write(f'{F12},{F13},{F23},{simulated_quaternion},{deviation_angle}\n')

    return deviation_angle

# Perform optimization
result = minimize(objective_function, [0.0, 0.0, 0.0], bounds=BOUNDS, method='L-BFGS-B')

# Plotting the deviation angle evolution
angles = np.loadtxt(RESULTS_CSV, delimiter=',', skiprows=1, usecols=4)
plt.plot(angles, marker='o')
plt.xlabel('Iteration')
plt.ylabel('Deviation Angle (degrees)')
plt.title('Deviation Angle Evolution')
plt.grid(True)
plt.savefig(os.path.abspath('workdir/deviation_angle_evolution.png'))
plt.show()

print('Optimization completed.')
print(f'Optimal F12, F13, F23: {result.x}')
print(f'Minimum deviation angle: {result.fun}')
