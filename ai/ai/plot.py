import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from infer import AiModel

class PointCloudVisualizer:
    def __init__(self, data_file, model_path, stats_path):
        # Load data
        self.rows = []
        with open(data_file, "r") as fh:
            for line in fh:
                if line.strip():
                    self.rows.append(json.loads(line))
        
        # Load model
        self.model = AiModel(
            model_path=model_path,
            stats_path=stats_path
        )
        
        self.current_frame = 0
        self.fig = None
        self.ax = None
        
    def plot_frame(self, frame_idx):
        if frame_idx < 0 or frame_idx >= len(self.rows):
            return
        
        self.current_frame = frame_idx
        row = self.rows[frame_idx]
        scan = row.get("scan") or []
        actual_steer = row.get("steer")
        
        # Get prediction
        predicted_steer = self.model.predict_steer(scan) if scan else 0.0
        
        # Clear previous plot
        if self.ax:
            self.ax.clear()
        else:
            self.fig, self.ax = plt.subplots(figsize=(10, 8))
        
        # Plot point cloud
        if scan:
            angles = []
            distances = []
            for angle_deg, dist_m in scan:
                angles.append(np.radians(angle_deg))
                distances.append(dist_m)
            
            # Convert polar to cartesian
            x = np.array(distances) * np.cos(angles)
            y = np.array(distances) * np.sin(angles)
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            # Plot points
            self.ax.scatter(x, y, c='blue', s=20, alpha=0.6, label='LiDAR points')
            
            # Plot robot position at origin
            self.ax.scatter(0, 0, c='red', s=100, marker='s', label='Robot', zorder=5)
            
            # Plot steering direction
            steering_angle = np.radians(predicted_steer * 90)  # Scale to ±90 degrees
            arrow_length = 1.0
            self.ax.arrow(0, 0, 
                          arrow_length * np.cos(steering_angle), 
                          arrow_length * np.sin(steering_angle),
                          head_width=0.1, head_length=0.1, fc='green', ec='green', 
                          linewidth=2, label='Predicted steering')
            
            if actual_steer is not None:
                actual_angle = np.radians(actual_steer * 90)
                self.ax.arrow(0, 0, 
                              arrow_length * np.cos(actual_angle) * 0.9, 
                              arrow_length * np.sin(actual_angle) * 0.9,
                              head_width=0.08, head_length=0.08, fc='orange', ec='orange', 
                              linewidth=2, linestyle='--', label='Actual steering', alpha=0.7)
        
        # Set labels and title
        self.ax.set_xlabel('X (meters)')
        self.ax.set_ylabel('Y (meters)')
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        
        # Title with frame info
        title = f'Frame {self.current_frame}/{len(self.rows)-1}'
        if actual_steer is not None:
            title += f' | Actual: {actual_steer:.4f} | Predicted: {predicted_steer:.4f}'
        else:
            title += f' | Predicted: {predicted_steer:.4f}'
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        
        plt.draw()
    
    def on_key(self, event):
        if event.key == 'right':
            self.plot_frame(self.current_frame + 1)
        elif event.key == 'left':
            self.plot_frame(self.current_frame - 1)
        elif event.key == 'home':
            self.plot_frame(0)
        elif event.key == 'end':
            self.plot_frame(len(self.rows) - 1)
    
    def run(self):
        self.plot_frame(0)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        plt.tight_layout()
        print("Controls:")
        print("  Left/Right Arrow: Navigate frames")
        print("  Home: Go to first frame")
        print("  End: Go to last frame")
        plt.show()


if __name__ == "__main__":
    visualizer = PointCloudVisualizer(
        data_file="test.jsonl",
        model_path=Path("models/my_model/model.onnx"),
        stats_path=Path("models/my_model/stats.json")
    )
    visualizer.run()