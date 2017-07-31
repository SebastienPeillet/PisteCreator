# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreatorDockWidget_slopegraph
                                 Slope graph for Qgis plugins
 ONF UI plugins to create tracks
                             -------------------
        begin                : 2017-07-25
        git sha              : $Format:%H$
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
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import random

class SlopeGraphicsView(QtGui.QDialog):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(SlopeGraphicsView, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.initplot()
        
    
    def initplot(self):
        ''' plot some random stuff '''
        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        # ax.hold(False)

        # plot data
        ax.set_xlim(0,50)
        ax.set_ylim(0,20)
        ax.set_xlabel('length')
        ax.plot([0,50],[10,10],'-',color='red')
        ax.plot([0,50],[4,4],'-',color='green')
        # ax.plot(x_list,y_list, '*-')

        # refresh canvas
        self.canvas.draw()

    def plot(self, x_list, y1_list, y2_list, y3_list):
        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.hold(False)

        # plot data
        ax.plot(x_list, y2_list, 'g.-', x_list, y3_list, 'g.-', x_list, y1_list, 'r*-')
        
        xmin,xmax = ax.get_xbound()
        ymin,ymax = ax.get_ybound()
        if ymax < 20 :
            ax.set_ylim(0,20)
        else :
            ax.set_ylim(0,ymax+1)
        ax.set_xlim(0,xmax+10)
        ax.add_line(Line2D([0,xmax+10],[10,10],color='red'))
        ax.add_line(Line2D([0,xmax+10],[4,4],color='green'))
        ax.set_xlabel('length')
        ax.set_ylabel('along slope(%)')
        # refresh canvas
        self.canvas.draw()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()