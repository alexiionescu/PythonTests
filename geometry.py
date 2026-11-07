#%%
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# 1. Set up the figure and axis
fig, ax = plt.subplots(figsize=(6, 6))

# 2. Define the vertices of a right triangle
A = np.array([1, 1])
B = np.array([4, 1])
C = np.array([4, 5])

# 3. Draw the segments (lines connecting the points)
# We append the first point at the end to close the triangle
x_coords = [A[0], B[0], C[0], A[0]]
y_coords = [A[1], B[1], C[1], A[1]]
ax.plot(x_coords, y_coords, color='black', linewidth=2)

# 4. Plot and label the vertices
ax.plot([A[0], B[0], C[0]], [A[1], B[1], C[1]], 'ro') # Red dots for vertices
ax.text(A[0]-0.2, A[1]-0.2, 'A', fontsize=14, weight='bold')
ax.text(B[0]+0.1, B[1]-0.2, 'B (90°)', fontsize=14, weight='bold')
ax.text(C[0]+0.1, C[1]+0.1, 'C', fontsize=14, weight='bold')

# 5. Draw an arc for Angle A (using Wedge)
# Angle A is roughly 53.13 degrees. The wedge goes from 0 to 53.13 degrees.
angle_arc = patches.Wedge(center=A, r=0.5, theta1=0, theta2=53.13, 
                          color='lightblue', alpha=0.5)
ax.add_patch(angle_arc)
ax.text(A[0]+0.6, A[1]+0.2, '53.13°', fontsize=12)

# 6. Draw a right-angle symbol at B
right_angle = patches.Rectangle((B[0]-0.3, B[1]), 0.3, 0.3, 
                                fill=False, edgecolor='red', linewidth=1.5)
ax.add_patch(right_angle)

# 7. Clean up the grid for a geometry textbook look
ax.set_xlim(0, 6)
ax.set_ylim(0, 6)
ax.set_aspect('equal') # Keeps geometry from distorting
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_title("Geometric Triangle Construction", fontsize=14)

plt.show()

# %%
