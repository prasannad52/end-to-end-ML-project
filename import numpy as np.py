import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.optimize import fsolve

# Orbital parameters (in astronomical units and years)
r_earth = 1.0          # Earth's orbital radius (AU)
r_mars = 1.524         # Mars' orbital radius (AU)
omega_earth = 360.0    # Earth's angular velocity (degrees/year)
omega_mars = 360.0 / 1.88  # Mars' angular velocity (degrees/year)
theta_m0 = 44.4        # Mars' initial phase angle at t=0 (degrees) for launch window

# Hohmann transfer orbit parameters
a_transfer = (r_earth + r_mars) / 2  # Semi-major axis (AU)
e = 1 - r_earth / a_transfer         # Eccentricity
T_transfer = 2 * np.pi * np.sqrt(a_transfer**3)  # Orbital period (years), assuming GM = 4π²
t_arrival = T_transfer / 2           # Transfer time to Mars (years)

# Function to solve Kepler's equation: M = E - e sin(E)
def solve_kepler(M, e):
    # Use fsolve with M as initial guess
    E = fsolve(lambda E: E - e * np.sin(E) - M, M)[0]
    return E

# Function to compute position on transfer orbit
def get_transfer_position(t, t_start, t_end, omega):
    """
    Compute spacecraft position on transfer orbit.
    t: current time, t_start: start of transfer, t_end: end of transfer, omega: argument of periapsis (degrees)
    """
    if t < t_start or t > t_end:
        return None
    dt = t - t_start
    transfer_duration = t_end - t_start
    # Mean anomaly M from 0 to π (outbound) or π to 2π (return)
    if t_start == 0:  # Outbound
        M = np.pi * (dt / transfer_duration)
    else:  # Return
        M = np.pi + np.pi * (dt / transfer_duration)
    E = solve_kepler(M, e)
    r = a_transfer * (1 - e * np.cos(E))
    # Compute true anomaly ν
    nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
    # Convert to Cartesian coordinates with orbit orientation
    omega_rad = omega * np.pi / 180
    x = r * np.cos(nu + omega_rad)
    y = r * np.sin(nu + omega_rad)
    z = 0  # Coplanar orbits
    return x, y, z

# Function to find departure time from Mars (next launch window)
def find_t_departure():
    def phase_condition(t):
        theta_e_future = (omega_earth * (t + t_arrival)) % 360
        theta_m_current = (omega_mars * t + theta_m0) % 360
        target = (theta_m_current - 180) % 360
        return (theta_e_future - target) % 360
    t = t_arrival
    step = 0.01
    while t < 10:  # Limit search to 10 years
        if abs(phase_condition(t)) < 0.1:  # Tolerance for alignment
            return t
        t += step
    return t_arrival + 1.246  # Fallback (approx waiting time)

# Compute key times
t_departure = find_t_departure()
t_return = t_departure + t_arrival

# Function to get spacecraft position
def get_spacecraft_position(t):
    if t < t_arrival:  # Outbound to Mars
        return get_transfer_position(t, 0, t_arrival, 0)
    elif t < t_departure:  # Waiting at Mars
        theta_mars = (omega_mars * t + theta_m0) % 360
        x = r_mars * np.cos(theta_mars * np.pi / 180)
        y = r_mars * np.sin(theta_mars * np.pi / 180)
        return x, y, 0
    elif t <= t_return:  # Return to Earth
        theta_d = (omega_mars * t_departure + theta_m0) % 360
        omega_return = (theta_d - 180) % 360
        return get_transfer_position(t, t_departure, t_return, omega_return)
    else:  # Back at Earth
        theta_earth = (omega_earth * t) % 360
        x = r_earth * np.cos(theta_earth * np.pi / 180)
        y = r_earth * np.sin(theta_earth * np.pi / 180)
        return x, y, 0

# Set up the 3D plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_zlim(-0.1, 0.1)
ax.set_xlabel('X (AU)')
ax.set_ylabel('Y (AU)')
ax.set_zlabel('Z (AU)')
ax.set_title('Earth-Mars-Earth Spacecraft Trajectory')

# Plot the Sun
ax.scatter([0], [0], [0], color='yellow', s=100, label='Sun')

# Plot Earth and Mars orbits
theta = np.linspace(0, 360, 100)
x_earth_orbit = r_earth * np.cos(theta * np.pi / 180)
y_earth_orbit = r_earth * np.sin(theta * np.pi / 180)
x_mars_orbit = r_mars * np.cos(theta * np.pi / 180)
y_mars_orbit = r_mars * np.sin(theta * np.pi / 180)
z_orbit = np.zeros(100)
ax.plot(x_earth_orbit, y_earth_orbit, z_orbit, 'b-', label='Earth Orbit')
ax.plot(x_mars_orbit, y_mars_orbit, z_orbit, 'r-', label='Mars Orbit')

# Initialize points
earth_point, = ax.plot([], [], [], 'bo', label='Earth', markersize=8)
mars_point, = ax.plot([], [], [], 'ro', label='Mars', markersize=8)
spacecraft_point, = ax.plot([], [], [], 'go', label='Spacecraft', markersize=6)

# Animation update function
def update(frame):
    t = frame
    # Earth position
    theta_earth = (omega_earth * t) % 360
    x_earth = r_earth * np.cos(theta_earth * np.pi / 180)
    y_earth = r_earth * np.sin(theta_earth * np.pi / 180)
    earth_point.set_data_3d([x_earth], [y_earth], [0])
    # Mars position
    theta_mars = (omega_mars * t + theta_m0) % 360
    x_mars = r_mars * np.cos(theta_mars * np.pi / 180)
    y_mars = r_mars * np.sin(theta_mars * np.pi / 180)
    mars_point.set_data_3d([x_mars], [y_mars], [0])
    # Spacecraft position
    pos = get_spacecraft_position(t)
    if pos:
        x, y, z = pos
        spacecraft_point.set_data_3d([x], [y], [z])
    return earth_point, mars_point, spacecraft_point

# Create animation
frames = np.linspace(0, t_return, 200)
ani = FuncAnimation(fig, update, frames=frames, interval=50, blit=False)

# Add legend and adjust view
ax.legend()
ax.view_init(elev=30, azim=45)  # Slight tilt for 3D effect

# Display the plot
plt.show()