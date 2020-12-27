# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreatorDockWidget
                                 A QGIS plugin
 ONF UI plugins to create tracks
                             -------------------
        begin                : 2017-04-24
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

import math

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget 
from qgis.PyQt.QtCore import pyqtSignal, QSettings

from qgis.core import QgsProject, QgsRasterLayer
from qgis.gui import QgsMapToolZoom

from .option_Dock import OptionDock
from .option_Dock_echap_mode import OptionDockEchap
from .slope_graph import SlopeGraphicsView

from ..Utils import SlopeMapTool, SelectMapTool


class PisteCreatorDockWidget(QDockWidget):

    closingPlugin = pyqtSignal()

    def __init__(self, plugin, iface, parent=None):
        """Constructor."""
        super(PisteCreatorDockWidget, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'PisteCreator_dockwidget_base.ui'), self)

        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.plugin = plugin
        self.listVectLayer()
        self.listRastLayer()
        self.graph_widget = SlopeGraphicsView()
        self.graphLayout.addWidget(self.graph_widget, 0, 0)
        self.TracksButton.clicked.connect(self.listVectLayer)
        self.DEMButton.clicked.connect(self.listRastLayer)
        self.EditButton.clicked.connect(self.slopeCalc)
        self.selectButton.clicked.connect(self.selectFeat)
        self.OptionButton.clicked.connect(self.openOption)
        self.canvas.layersChanged.connect(self.layersUpdate)
        self.desacButton.setChecked(True)
        self.desacButton.clicked.connect(lambda: self.changeAssistedMode('c'))
        self.cloisButton.clicked.connect(lambda: self.changeAssistedMode('c'))
        self.echapButton.clicked.connect(lambda: self.changeAssistedMode('e'))

    def changeAssistedMode(self,mode):
        self.iface.mapCanvas().setMapTool(QgsMapToolZoom(self.canvas, False))
        self.graph_widget.plot([],[],[],[],mode)

    def listRastLayer(self):
        """List raster inputs for the DEM selection"""

        # clear list and index
        self.DEMInput.clear()
        self.DEMInput.clearEditText()
        self.rast_list = []
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        index = 0
        for layer in layers:
            if layer.type() == 1:
                layer_list.append(layer.name())
                self.rast_list.append(index)
            index += 1
        self.DEMInput.addItems(layer_list)

    def listVectLayer(self):
        """List line layer for the track selection"""

        # clear list and index
        self.TracksInput.clear()
        self.TracksInput.clearEditText()
        self.vect_list = []
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        index = 0
        for layer in layers:
            if layer.type() == 0:
                if layer.geometryType() == 1:
                    layer_list.append(layer.name())
                    self.vect_list.append(index)
            index += 1
        self.TracksInput.addItems(layer_list)

    def displayXY(
        self, a, b, c, d, geom, a_slope, c_l_slope, c_r_slope, graph_draw
    ):
        """Check output values from the edit maptool (callback function)"""

        if a is not None:
            self.AlongResult.setText(str(a)+'%')
        if b is not None:
            self.LeftCrossResult.setText(str(b)+'%')
        if c is not None:
            self.RightCrossResult.setText(str(c)+'%')
        if d is not None:
            self.LengthResult.setText(str(d))
        if graph_draw is True:
            self.updateGraph(geom, a_slope, c_l_slope, c_r_slope)

    def openOption(self):
        """Open the options box"""
        if self.echapButton.isChecked() == True :
            self.optionDock = OptionDockEchap(self.plugin, self.graph_widget, self.canvas)
            self.optionDock.show()
        elif self.cloisButton.isChecked() == True :
            self.optionDock = OptionDock(self.plugin, self.graph_widget, self.canvas)
            self.optionDock.show()
        elif self.desacButton.isChecked() == True :
            self.optionDock = OptionDock(self.plugin, self.graph_widget, self.canvas)
            self.optionDock.show()
        return None

    def selectFeat(self):
        """Activate the select tools to review track graph"""

        self.iface.mapCanvas().setMapTool(QgsMapToolZoom(self.canvas, False))
        st = None
        # 1 Get the vector layer
        linesLayer = QgsProject.instance().mapLayersByName(self.TracksInput.currentText())[0]
        # 2 Get the raster layer
        DEMLayer = QgsProject.instance().mapLayersByName(self.DEMInput.currentText())[0]

        dem = DEMLayer
        if not dem.isValid():
            # fix_print_with_import
            print("Layer failed to load!")

        # 3
        settings = QSettings()
        side_distance = int(settings.value(
            'PisteCreator/calculation_variable/side_distance', 10
        ))
        interpolate_act = bool(settings.value(
            'PisteCreator/calculation_variable/interpolate_act', True
        ))

        # 4 Activate Maptools

        self.PisteCreatorTool = SelectMapTool(
            self.iface,  self.updateGraph, linesLayer,
            dem, side_distance, interpolate_act
        )
        self.iface.mapCanvas().setMapTool(self.PisteCreatorTool)

    def slopeCalc(self):
        """Activate the edit tool"""

        self.iface.mapCanvas().setMapTool(QgsMapToolZoom(self.canvas, False))
        ct = None
        # 1 Get the vector layer
        linesLayer = QgsProject.instance().mapLayersByName(self.TracksInput.currentText())[0]
        linesLayer.startEditing()
        # 2 Get the raster layer
        DEMLayer = QgsProject.instance().mapLayersByName(self.DEMInput.currentText())[0]
        
        dem = DEMLayer
        if not dem.isValid():
            # fix_print_with_import
            print("Layer failed to load!")

        # 3
        settings = QSettings()
        side_distance = int(settings.value(
            'PisteCreator/calculation_variable/side_distance', 6
        ))
        tolerated_a_slope = int(settings.value(
            'PisteCreator/graphical_visualisation/tolerated_a_slope', 10
        ))
        tolerated_c_slope = int(settings.value(
            'PisteCreator/graphical_visualisation/tolerated_c_slope', 4
        ))
        max_length = int(settings.value(
            'PisteCreator/graphical_visualisation/max_length', 50
        ))
        max_length_hold = bool(settings.value(
            'PisteCreator/graphical_visualisation/max_length_hold', False
        ))
        swath_distance = int(settings.value(
            'PisteCreator/graphical_visualisation/swath_distance', 30
        ))
        swath_display = bool(settings.value(
            'PisteCreator/graphical_visualisation/swath_display', True
        ))
        interpolate_act = bool(settings.value(
            'PisteCreator/calculation_variable/interpolate_act', True
        ))
        t_color = settings.value(
            'PisteCreator/graphical_visualisation/t_color', '#00d003'
        )
        f_color = settings.value(
            'PisteCreator/graphical_visualisation/f_color', '#ff0000'
        )
        tl_color = settings.value(
            'PisteCreator/graphical_visualisation/tl_color', '#236433'
        )
        fl_color = settings.value(
            'PisteCreator/graphical_visualisation/fl_color', '#b80000'
        )
        b_color = settings.value(
            'PisteCreator/graphical_visualisation/b_color', '#0fff33'
        )
        a_color = settings.value(
            'PisteCreator/graphical_visualisation/a_color', '#48b0d2'
        )
        if self.echapButton.isChecked() == True :
            assisted_mode = 'e'
        elif self.cloisButton.isChecked() == True :
            assisted_mode = 'c'
        elif self.desacButton.isChecked() == True :
            assisted_mode = None
        # 4 Activate Maptools
        self.PisteCreatorTool = SlopeMapTool(
            self.iface,  self.displayXY, linesLayer, dem, side_distance,
            tolerated_a_slope, tolerated_c_slope, max_length, swath_distance,
            max_length_hold, swath_display, interpolate_act, t_color, f_color,
            tl_color, fl_color, b_color, a_color, assisted_mode
        )
        self.iface.mapCanvas().setMapTool(self.PisteCreatorTool)

    def updateGraph(self, geom, a_slope, c_l_slope, c_r_slope):
        """Update the track graph, use as a callback function \
        for the PisteCreator Edit Maptools"""

        length = 0
        length_list = [0]
        len_geom = len(geom)
        if len_geom != 0:
            for i in range(0, len_geom-1):
                if i + 1 <= len_geom:
                    pt1 = geom[i]
                    pt2 = geom[i+1]
                    azimuth = pt1.azimuth(pt2)
                    length += math.sqrt(pt1.sqrDist(pt2))
                    length_list.append(length)
        else:
            del length_list[-1]
        if self.echapButton.isChecked() == True :
            assisted_mode = 'e'
        elif self.cloisButton.isChecked() == True :
            assisted_mode = 'c'
        elif self.desacButton.isChecked() == True :
            assisted_mode = None
        self.graph_widget.plot(length_list, a_slope, c_l_slope, c_r_slope, assisted_mode)

    def layersUpdate(self):
        track_text = self.TracksInput.currentText()
        dem_text = self.DEMInput.currentText()
        self.listRastLayer()
        self.listVectLayer()
        track_ind = self.TracksInput.findText(track_text)
        dem_ind = self.DEMInput.findText(dem_text)
        if track_ind != -1 :
            self.TracksInput.setCurrentIndex(track_ind)
        if dem_ind != -1 :
            self.DEMInput.setCurrentIndex(dem_ind)
        return None

    def closeEvent(self, event):
        """Clove event"""
        self.closingPlugin.emit()
        event.accept()
