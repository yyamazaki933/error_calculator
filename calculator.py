#!/usr/bin/env python3
import os
import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5 import uic, QtWidgets

import scripts.lateral_error as lateral_error


def open_file():
    home_dir = os.getenv('HOME')
    file = QFileDialog.getOpenFileName(ui_main, 'Open CSV File', home_dir, 'CSV File (*.csv)')[0]
    return file


def pb_ref_call():
    file = open_file()
    if file == '':
        return
    ui_main.le_ref.setText(file)


def pb_test_call():
    file = open_file()
    if file == '':
        return
    ui_main.le_test.setText(file)
    

def pb_run_call():
    mode = mode_group.checkedId()
    show_error = ui_main.chb_err.checkState()
    # plot_only = ui_main.chb_plt.checkState()

    read_file()

    if mode == 1: # lat and lon
        lateral_error.error_calc(ref_data, test_data, mode="time_sync", log_file=log_filename, progress=ui_main.progress)
        plot(show_error)
    if mode == 2: # lat only
        lateral_error.error_calc(ref_data, test_data, mode="find_neighbor", log_file=log_filename, progress=ui_main.progress)
        plot(show_error)
    if mode == 3: # plot only
        plot(show_error)


def read_file():
    global out_dir
    global ref_data
    global test_data
    global log_filename
    
    ref_filename = ui_main.le_ref.text()
    test_filename = ui_main.le_test.text()

    ref_data = pd.read_csv(ref_filename)
    test_data = pd.read_csv(test_filename)
    out_dir = os.path.dirname(test_filename)
    log_filename = test_filename.replace(".csv", "_log.csv")

    test_data["msg.header.stamp"] = lateral_error.get_concatenated_stamps(test_data)
    ref_data["msg.header.stamp"] = lateral_error.get_concatenated_stamps(ref_data)


def plot(show_error=False):
    lateral_error.plot_2d(ref_data, test_data, show_error, out_dir + '/route_plot.html')
    lateral_error.plot_xy_err(test_data, out_dir + '/err_plot_xy.html')
    lateral_error.plot_z_err(test_data, out_dir + '/err_plot_z.html')


if __name__ == '__main__':
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    app = QApplication(sys.argv)
    ui_main = uic.loadUi(SCRIPT_DIR + '/ui/main.ui')
    ui_main.pb_ref.clicked.connect(pb_ref_call)
    ui_main.pb_test.clicked.connect(pb_test_call)
    ui_main.pb_run.clicked.connect(pb_run_call)
    ui_main.show()

    mode_group = QtWidgets.QButtonGroup()
    mode_group.addButton(ui_main.rb_latlon, 1)
    mode_group.addButton(ui_main.rb_lat, 2)
    mode_group.addButton(ui_main.rb_2d, 3)

    sys.exit(app.exec())