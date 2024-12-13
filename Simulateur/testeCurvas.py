import matplotlib.pyplot as plt

import numpy as np
from scipy.integrate import cumtrapz
from scipy.interpolate import interp1d

def reparametrize_arc_length(func, x_domain, resolution):
    """
    Reparametrize a curve based on arc length to generate evenly spaced points.
    
    func: callable - The curve function y = f(x).
    x_domain: tuple - The domain of x (e.g., (x_min, x_max)).
    resolution: int - Number of points to generate.
    
    Returns:
    np.ndarray - Reparametrized x and y points.
    """
    # Generate initial uniform sampling of x
    x_vals = np.linspace(x_domain[0], x_domain[1], 10 * resolution)
    y_vals = np.array([func(x) for x in x_vals])

    # Calculate the derivative dy/dx
    dydx = np.gradient(y_vals, x_vals)

    # Compute arc length using cumulative trapezoidal integration
    arc_length = cumtrapz(np.sqrt(1 + dydx**2), x_vals, initial=0)

    # Generate uniform samples in arc length space
    uniform_arc_length = np.linspace(0, arc_length[-1], resolution)

    # Interpolate to find corresponding x values
    interp_x = interp1d(arc_length, x_vals, kind='linear')
    reparam_x = interp_x(uniform_arc_length)

    # Evaluate the curve at the new x values
    reparam_y = np.array([func(x) for x in reparam_x])

    return reparam_x, reparam_y

# Define the curve
def curve(x):
    return np.sqrt(1 - (x - 0.5)**2)

# Original domain
x_domain = (0, 1)

# Generate points with reparametrization
x_reparam, y_reparam = reparametrize_arc_length(curve, x_domain, resolution=100)

# Plot
plt.plot(x_reparam, y_reparam, label="Reparametrized Curve", marker='o', markersize=2)
plt.title("Reparametrized Curve with Uniform Arc Length")
plt.xlabel("x")
plt.ylabel("y")
plt.legend()
plt.grid()
plt.show()

