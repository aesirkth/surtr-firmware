import json
import sys
import matplotlib.pyplot as plt

if len(sys.argv) != 2:
    print("Usage: plot2.py [json_file]")
    sys.exit(1)

# Load JSON data
with open(sys.argv[1], 'r') as f:
    data = json.load(f)

# Get all categories (keys)
categories = sorted(data.keys())

# Create subplots - arrange in a grid
num_categories = len(categories)
cols = 3
rows = (num_categories + cols - 1) // cols  # Ceiling division

fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
if num_categories == 1:
    axes = [axes]
else:
    axes = axes.flatten()

# Plot each category
for idx, category in enumerate(categories):
    ax = axes[idx]
    time_series = data[category][0]
    data_series = data[category][1]
    
    ax.plot(time_series, data_series)
    ax.set_title(category)
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.grid(True)

# Hide unused subplots
for idx in range(num_categories, len(axes)):
    axes[idx].set_visible(False)

plt.tight_layout()
plt.show()

c_start = 4
c_end = 20

# Create a fullscreen plot of value110
if 'value110' in data:
    fig2 = plt.figure(figsize=(16, 9))  # Large figure size for fullscreen-like display
    fig2.canvas.manager.set_window_title('value110 - Fullscreen')
    
    time_series = data['value110'][0]
    raw_data = data['value110'][1]
    data_series = [100 * (x - c_start) / (c_end - c_start) for x in raw_data]
    
    plt.plot(time_series, data_series)
    plt.title('value110', fontsize=16)
    plt.xlabel('Time', fontsize=14)
    plt.ylabel('Value', fontsize=14)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print("Warning: 'value110' not found in data")

