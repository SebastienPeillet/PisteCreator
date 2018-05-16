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

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import ConfigParser


class GrumpyConfigParser(ConfigParser.ConfigParser):
    """Virtually identical to the original method, but delimit keys
    and values with '=' instead of ' = '"""
    def write(self, fp):
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):

                    key = "=".join((key, str(value).replace('\n', '\n\t')))

                fp.write("%s\n" % (key))
        fp.write("\n")


class SlopeGraphicsView(QtGui.QDialog):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor"""
        super(SlopeGraphicsView, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ConfigParser = None
        self.tolerated_slope = None
        self.initPars()
        self.initplot()

    def initPars(self):
        self.ConfigParser = GrumpyConfigParser()
        self.ConfigParser.optionxform = str
        configFilePath = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'option.cfg')
        self.ConfigParser.read(configFilePath)
        self.tolerated_a_slope = self.ConfigParser.getint(
            'graphical_visualisation', 'tolerated_a_slope')
        self.tolerated_c_slope = self.ConfigParser.getint(
            'graphical_visualisation', 'tolerated_c_slope')

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

        # discards the old graph
        ax.hold(False)

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
