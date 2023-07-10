#!/usr/bin/env python3
import os
import sys
import numpy as np
import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import Range1d


def error_calc(ref_data, test_data, mode, progress = None, log_file = "error_calc.csv" ):
    elapsed_t=[]
    xy_errors=[]
    z_errors=[]
    lateral_points_x=[]
    lateral_points_y=[]

    start_t = None
    idx_end = len(test_data)
    if progress:
        progress.setRange(0, idx_end)
    for idx, row in test_data.iterrows():
        print(idx, '/', idx_end)
        if progress:
            progress.setValue(idx)

        current_t = row['msg.header.stamp']
        if idx == 0:
            start_t = current_t
        elapsed_t.append(current_t - start_t)

        test_p = np.array([row['x'], row['y'], row['z']])

        if mode == "find_neighbor":
            min_points = get_neighbor_point(test_p, ref_data)
        elif mode == "time_sync":
            min_points = get_timesync_point(current_t, ref_data)

        ref1 = min_points[-1]
        ref2 = min_points[-2]

        lateral_p, lateral_dist, z_err = calc_distance_and_neighbor_point(ref1, ref2, test_p)

        xy_errors.append(lateral_dist)
        z_errors.append(z_err)
        lateral_points_x.append(lateral_p[0])
        lateral_points_y.append(lateral_p[1])
    
    test_data['elapsed_time'] = elapsed_t
    test_data['xy_err'] = xy_errors
    test_data['z_err'] = z_errors
    test_data['error_point.x'] = lateral_points_x
    test_data['error_point.y'] = lateral_points_y
    test_data.to_csv(log_file, index=False)


def get_neighbor_point(target, find_src):
    min_dist = None
    min_p = []

    a = target

    for idx, p in find_src.iterrows():
        b = np.array([p['x'], p['y']])
        ab = b - a
        dist = np.linalg.norm(ab)

        if min_dist == None:
            min_dist = dist
            min_p.append(b)
        elif dist < min_dist:
            min_dist = dist
            min_p.append(b)
    return min_p


def get_timesync_point(time, find_src):
    min_p = []

    sync_idx = find_src["msg.header.stamp"].sub(time).abs().idxmin()
    min1 = find_src.iloc[sync_idx]
    min2 = find_src.iloc[sync_idx - 1]
    min_p.append(np.array([min1['x'], min1['y'], min1['z']]))
    min_p.append(np.array([min2['x'], min2['y'], min2['z']]))
    
    return min_p


def calc_distance_and_neighbor_point(a_3d, b_3d, p_3d):
    a = a_3d[0:2]
    b = b_3d[0:2]
    p = p_3d[0:2]
    ap = p - a
    ab = b - a
    ai_norm = np.dot(ap, ab)/np.linalg.norm(ab)
    neighbor_point = a + (ab)/np.linalg.norm(ab)*ai_norm
    xy_err = np.linalg.norm(p - neighbor_point)

    z_err = p_3d[2] - a_3d[2]
    return neighbor_point, xy_err, z_err


def get_concatenated_stamps(data):
    return data["sec"] + (data["nanosec"] / 1000000000)


def plot_2d(ref_data, test_data, show_error, out_filename):
    p = figure(x_axis_label='X', y_axis_label='Y', title='2D Plot', match_aspect=True)

    p.line(ref_data['x'], ref_data['y'], line_color='blue', legend_label='REF')
    p.circle(ref_data['x'], ref_data['y'], line_color='blue', line_width=5)

    p.line(test_data['x'], test_data['y'], line_color='red', legend_label='TEST')
    p.circle(test_data['x'], test_data['y'], line_color='red', line_width=5)

    if show_error:
        p.cross(test_data['error_point.x'], test_data['error_point.y'], color='black', legend_label='rateral_point', size=16)
        for idx, row in test_data.iterrows():
            x1 = row['x']
            x2 = row['error_point.x']
            y1 = row['y']
            y2 = row['error_point.y']
            p.line([x1, x2], [y1, y2], line_color='black')

    output_file(out_filename)
    show(p)


def plot_xy_err(test_data, out_filename):
    p = figure(x_axis_label='Elapsed Time[s]', y_axis_label='XY Error[m]', title='Error Plot')
    p.width = 1200
    p.y_range = Range1d(0, 0.5)
    p.line(test_data['elapsed_time'], test_data['xy_err'], line_color='blue')
    output_file(out_filename)
    show(p)


def plot_z_err(test_data, out_filename):
    p = figure(x_axis_label='Elapsed Time[s]', y_axis_label='Height Error[m]', title='Error Plot')    
    p.width = 1200
    p.y_range = Range1d(-0.5, 0.5)
    p.line(test_data['elapsed_time'], test_data['z_err'], line_color='blue')
    output_file(out_filename)
    show(p)


if __name__ == '__main__':
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    REF_FILE = sys.argv[1]
    TEST_FILE = sys.argv[2]
    show_error = False

    ref_data = pd.read_csv(REF_FILE)
    test_data = pd.read_csv(TEST_FILE)
    output_dir = os.path.dirname(TEST_FILE)

    error_calc(ref_data, test_data)

    plot_2d(ref_data, test_data, show_error, output_dir + '/route_plot.html')
    plot_xy_err(test_data, output_dir + '/err_plot_xy.html')
    plot_z_err(test_data, output_dir + '/err_plot_z.html')
