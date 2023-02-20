#!/usr/bin/env python3
import os
import sys
import numpy as np
import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import Range1d

REF_FILE = sys.argv[1]
TEST_FILE = sys.argv[2]
show_error = False

def error_calc(ref_data, test_data):
    elapsed_t=[]
    lateral_errors=[]
    lateral_points_x=[]
    lateral_points_y=[]

    start_t = None
    idx_end = len(test_data)
    for idx, row in test_data.iterrows():
        print(idx, '/', idx_end)

        current_t = row['msg.header.stamp']
        if idx == 0:
            start_t = current_t
        elapsed_t.append(current_t - start_t)

        test = np.array([row['x'], row['y']])
        min_points = get_neighbor_point(test, ref_data)
        ref1 = min_points[-1]
        ref2 = min_points[-2]

        lateral_p, lateral_dist = calc_distance_and_neighbor_point(ref1, ref2, test)

        lateral_errors.append(lateral_dist)
        lateral_points_x.append(lateral_p[0])
        lateral_points_y.append(lateral_p[1])
    
    test_data['elapsed_time'] = elapsed_t
    test_data['lateral_error'] = lateral_errors
    test_data['lateral_point.x'] = lateral_points_x
    test_data['lateral_point.y'] = lateral_points_y

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
            

def calc_distance_and_neighbor_point(a, b, p):
    ap = p - a
    ab = b - a
    ai_norm = np.dot(ap, ab)/np.linalg.norm(ab)
    neighbor_point = a + (ab)/np.linalg.norm(ab)*ai_norm
    distance = np.linalg.norm(p - neighbor_point)
    return neighbor_point, distance


def plot_2d(ref_data, test_data):
    p = figure(x_axis_label='X', y_axis_label='Y', title='2D Plot', match_aspect=True)

    p.line(ref_data['x'], ref_data['y'], line_color='blue', legend_label='REF')
    p.circle(ref_data['x'], ref_data['y'], line_color='blue', line_width=5)

    p.line(test_data['x'], test_data['y'], line_color='red', legend_label='TEST')
    p.circle(test_data['x'], test_data['y'], line_color='red', line_width=5)

    if show_error:
        p.cross(test_data['lateral_point.x'], test_data['lateral_point.y'], color='black', legend_label='rateral_point', size=16)
        for idx, row in test_data.iterrows():
            x1 = row['x']
            x2 = row['lateral_point.x']
            y1 = row['y']
            y2 = row['lateral_point.y']
            p.line([x1, x2], [y1, y2], line_color='black')

    output_file(output_dir + '/2d_plot.html')
    show(p)


def plot_value(x_data, x_label, y_data, y_label):
    p = figure(x_axis_label=x_label, y_axis_label=y_label, title='Time Plot')    
    p.y_range = Range1d(0, 1)
    p.line(x_data, y_data, line_color='blue')
    output_file(output_dir + '/value.html')
    show(p)


if __name__ == '__main__':
    # current dir
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    ref_data = pd.read_csv(REF_FILE)
    test_data = pd.read_csv(TEST_FILE)

    output_dir = os.path.dirname(TEST_FILE)

    error_calc(ref_data, test_data)
    plot_2d(ref_data, test_data)
    plot_value(test_data['elapsed_time'], 'elapsed time[s]', test_data['lateral_error'], 'lateral error[m]')

    test_data.to_csv(TEST_FILE.replace('.csv', '_tmp.csv'), index=False)