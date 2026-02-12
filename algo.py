import json
import math

import numpy as np
from scipy.spatial import KDTree

lidar_to_front_wheel = 0.03
front_to_back_wheel = 0.259

def kdfilter(pts, radius=0.4, min_neighbors=6):
    if len(pts) < min_neighbors:
        return pts
    tree = KDTree(pts)
    mask = np.zeros(len(pts), dtype=bool)
    for i, p in enumerate(pts):
        idxs = tree.query_ball_point(p, r=radius)
        if len(idxs) - 1 >= min_neighbors:
            mask[i] = True
    return pts[mask]

def roi(data, anglelim = 70, rclose = 0.2, rfar = 5):
    dataout = []
    for angle_deg, r in data:
        if angle_deg > 90 - anglelim and angle_deg < anglelim  + 90 and r and r > rclose and r < rfar:
            dataout.append((180 - angle_deg, r))
    dataout.sort(key = lambda x : x[0])
    return dataout

def convert(data):
    pts = []
    for angle_deg, r in data:
        a = math.radians(angle_deg)
        x = r * math.cos(a)
        y = r * math.sin(a)
        pts.append((x, y))
    return pts

def neighbormaxdiff_ind(data):
    dmaxsquared = 0
    ind = -1
    for i in range(1, len(data)):
        a = data[i - 1]
        b = data[i]
        d_sq = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
        if d_sq > dmaxsquared:
            dmaxsquared = d_sq
            ind = i
    return [ind - 1, ind]

def circle_from_3pts(p1, p2, p3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    d = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return None
    x1sq = x1 * x1 + y1 * y1
    x2sq = x2 * x2 + y2 * y2
    x3sq = x3 * x3 + y3 * y3
    ux = (x1sq * (y2 - y3) + x2sq * (y3 - y1) + x3sq * (y1 - y2)) / d
    uy = (x1sq * (x3 - x2) + x2sq * (x1 - x3) + x3sq * (x2 - x1)) / d
    r = math.hypot(ux - x1, uy - y1)
    return ux, uy, r

def calculatesteer(data):
    data = roi(data)
    xy_data = convert(data)
    if len(xy_data) < 3:
        return 0.0
    xy_data = kdfilter(np.array(xy_data), 0.1, 2)
    p1_ind, p2_ind = neighbormaxdiff_ind(xy_data) 
    p3 = [(xy_data[p1_ind][0] + xy_data[p2_ind][0])/2, 
            (xy_data[p1_ind][1] + xy_data[p2_ind][1])/2]
    p = [p3, [-front_to_back_wheel-lidar_to_front_wheel, 0], [-lidar_to_front_wheel, 0]]
    ux, uy, r = circle_from_3pts(p[0], p[1], p[2])
    steer = math.atan2(front_to_back_wheel, r) * 180.0 / math.pi  
    if uy < 0:
       steer = -steer 
    return steer

if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.patches import Circle
    from matplotlib.patches import Arc
    frames = []
    p12 = []
    steer = [] 
    with open("cw.jsonl") as f:
        for line in f:
            data = json.loads(line)
            data_bck = list(data["scan"])
            data = roi(data["scan"])
            xy_data = convert(data)
            xy_data = kdfilter(np.array(xy_data))
            xy_data = kdfilter(np.array(xy_data), 0.1, 2)
            p1_ind, p2_ind = neighbormaxdiff_ind(xy_data)
            
            p3 = [(xy_data[p1_ind][0] + xy_data[p2_ind][0])/2, 
                    (xy_data[p1_ind][1] + xy_data[p2_ind][1])/2]
            p = [p3, [-front_to_back_wheel-lidar_to_front_wheel, 0], [-lidar_to_front_wheel, 0]]
            p12.append(p)
            steer.append(calculatesteer(data_bck)) 
            frames.append(xy_data)
            
    fig, ax = plt.subplots()
    sc = ax.scatter([], [], s=5)
    sc_red = ax.scatter([], [], s=20, c="red")
    ax.set_aspect("equal")
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.grid(True)

    def on_key(event):
        global frame_idx
        if event.key == "right":
            frame_idx = (frame_idx + 1) % len(frames)
        elif event.key == "left":
            frame_idx = (frame_idx - 1) % len(frames)
        update()

    frame_idx = 0
    def update(i=None):
        sc.set_offsets(frames[frame_idx] )
        sc_red.set_offsets(p12[frame_idx])
        s = steer[frame_idx]
        
        ax.set_title(f"Frame {frame_idx}, steer = {s:.2} Deg")
        
        front_wheel_pos = p12[frame_idx][2]  # Front wheel position
        steer_angle = math.radians(steer[frame_idx])
        dx = math.cos(steer_angle) * 3.0
        dy = math.sin(steer_angle) * 3.0        
        for patch in list(ax.patches):
            patch.remove()
        for collection in list(ax.collections):
            if collection not in [sc, sc_red]:
                collection.remove()
        ax.quiver(front_wheel_pos[0], front_wheel_pos[1], dx, dy, 
                 angles='xy', scale_units='xy', color='orange', width=0.01, scale=1)
        
        ux, uy, r = circle_from_3pts(p12[frame_idx][0], p12[frame_idx][1], p12[frame_idx][2])
        p1, p2 = p12[frame_idx][0], p12[frame_idx][1]
        ux, uy, r = circle_from_3pts(p12[frame_idx][0], p12[frame_idx][1], p12[frame_idx][2])
        
        a1 = math.degrees(math.atan2(p1[1] - uy, p1[0] - ux))
        a2 = math.degrees(math.atan2(p2[1] - uy, p2[0] - ux))
        a1 = (a1 + 360) % 360
        a2 = (a2 + 360) % 360
        if (a2 - a1) % 360 > 180:
            a1, a2 = a2, a1
        arc = Arc(
            (ux, uy),
            2 * r,
            2 * r,
            angle=0,
            theta1=a1,
            theta2=a2,
            color="green",
            linewidth=2
        )
        ax.add_patch(arc)
        fig.canvas.draw_idle()
        return sc,

    fig.canvas.mpl_connect("key_press_event", on_key)
    update()
    plt.show()
