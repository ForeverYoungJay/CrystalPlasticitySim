import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution
from damask_simulation import run_damask_simulation
from damask_results import calculate_mse
from damask_yaml import update_material_properties

# Define the paths to the necessary files
workdir = os.path.abspath('workdir')
material_file = os.path.join(workdir, 'Ni3Al17-A1-material.yaml')
experimental_file = os.path.join(workdir, 'Ni3Al17-A1.txt')
load_file = os.path.join(workdir, 'load.yaml')
grid_file = os.path.join(workdir, 'grid.vti')

# Define the bounds for the parameters
bounds = [
    (10, 80),       # Stress exponent for slip
    (5e6, 20e6),    # Initial critical shear stress for slip (in Pascals)
    (10e6, 50e6),   # Maximum critical shear stress for slip (in Pascals)
    (100e6, 10e9)   # Initial hardening modulus for slip-slip interactions (in Pascals)
]

# Define the optimization function

def optimization_function(params):
    try:
        n_sl, xi_0_sl, xi_inf_sl, h_0_sl_sl = params
        new_values = {
            'n_sl': int(n_sl),
            'xi_0_sl': xi_0_sl,
            'xi_inf_sl': xi_inf_sl,
            'h_0_sl-sl': h_0_sl_sl
        }

        # Update the material properties
        updated_material_file = update_material_properties(material_file, new_values)

        # Run the DAMASK simulation
        result_file = run_damask_simulation(json.dumps({
            'load_file': load_file,
            'grid_file': grid_file,
            'material_file': updated_material_file
        }))

        # Calculate the error
        error = calculate_mse(experimental_file, result_file)

        # Log the results
        log_results(params, error)

        return error
    except Exception as e:
        print(f"Error during optimization function: {e}")
        return np.inf

# Function to log the results of each iteration
def log_results(params, error):
    log_file = os.path.join(workdir, 'optimization_results.csv')
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write('n_sl,xi_0_sl,xi_inf_sl,h_0_sl_sl,error\n')
    with open(log_file, 'a') as f:
        f.write(f"{params[0]},{params[1]},{params[2]},{params[3]},{error}\n")

# Run the optimization
try:
    result = differential_evolution(optimization_function, bounds, strategy='best1bin', maxiter=100, popsize=15, tol=0.01)

    # Plot the error improvement
    def plot_error_improvement():
        df = pd.read_csv(os.path.join(workdir, 'optimization_results.csv'))
        plt.figure(figsize=(10, 6))
        plt.plot(df['error'], marker='o')
        plt.xlabel('Iteration')
        plt.ylabel('Error')
        plt.title('Error Improvement Over Iterations')
        plt.grid(True)
        plt.savefig(os.path.join(workdir, 'error_improvement.png'))
        plt.show()

    plot_error_improvement()

    print("Optimization completed. Best parameters found:")
    print(f"n_sl: {result.x[0]}, xi_0_sl: {result.x[1]}, xi_inf_sl: {result.x[2]}, h_0_sl-sl: {result.x[3]}")
    print(f"Minimum error: {result.fun}")
except Exception as e:
    print(f"Error during optimization process: {e}")
