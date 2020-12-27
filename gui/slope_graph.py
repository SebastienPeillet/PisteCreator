# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreatorDockWidget_slopegraph
                                Slope graph for Qgis plugins
 Tracks chart display
                             -------------------
        begin                : 2017-07-25
        last                 : 2017-10-20
        copyright            : (C) 2017 by Peillet Sebastien
        email                : peillet.seb@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from future import standard_library
standard_library.install_aliases()
from builtins import str
import os

from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class SlopeGraphicsView(QDialog):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor"""
        super(SlopeGraphicsView, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.settings = None
        self.tolerated_slope = None
        self.initPars()
        self.initplot()

    def initPars(self):
        self.settings = QSettings()
        self.tolerated_a_slope = int(self.settings.value(
            'PisteCreator/graphical_visualisation/tolerated_a_slope', 10))
        self.tolerated_c_slope = int(self.settings.value(
            'PisteCreator/graphical_visualisation/tolerated_c_slope', 4))

    def initplot(self):
        ''' plot some random stuff '''
        # create an axis
        ax = self.figure.add_subplot(111)

        # plot data
        ax.set_xlim(0, 50)
        ax.set_ylim(0, self.tolerated_a_slope+10)
        ax.set_xlabel('length')
        ax.set_ylabel('slope(%)')
        ax.plot(
            [0, 50],
            [self.tolerated_a_slope, self.tolerated_a_slope],
            'r-',
            [0, 50],
            [self.tolerated_c_slope, self.tolerated_c_slope],
            'g-'
        )

        # refresh canvas
        self.canvas.draw()

    def plot(self, x_list, y1_list, y2_list, y3_list, assisted_mode):
        # create an axis
        ax = self.figure.add_subplot(111)

        # plot data
        ax.plot(
            x_list, y2_list, 'g.-', x_list, y3_list,
            'g.-', x_list, y1_list, 'r*-'
        )

        xmin, xmax = ax.get_xbound()
        ymin, ymax = ax.get_ybound()
        if ymax < self.tolerated_a_slope + 10:
            ax.set_ylim(0, self.tolerated_a_slope + 10)
        else:
            ax.set_ylim(0, ymax + 1)
        ax.set_xlim(0, xmax + 10)
        ax.add_line(
            Line2D(
                [0, xmax + 10],
                [self.tolerated_a_slope, self.tolerated_a_slope],
                color='red')
            )
        if assisted_mode != 'e' :
            ax.add_line(
                Line2D(
                    [0, xmax + 10],
                    [self.tolerated_c_slope, self.tolerated_c_slope],
                    color='green')
                )
        ax.set_xlabel('length')
        ax.set_ylabel('slope(%)')
        # refresh canvas
        self.canvas.draw()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
