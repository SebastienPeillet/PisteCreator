# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreatorDockWidget_OptionDock
                                Option dock for Qgis plugins
 Option dock initialize
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
from builtins import range
import os

from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings
from qgis.gui import QgsColorButton


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return list(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

class OptionDock(QDialog):

    closingPlugin = pyqtSignal()

    def __init__(self, plugin, graph_widget, canvas, parent=None):
        """Constructor."""
        super(OptionDock, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'Option_dock.ui'), self)
        self.settings = QSettings()
        self.initConfig()
        self.graph_widget = graph_widget
        self.PisteCreatorTool = plugin.PisteCreatorTool
        self.canvas = canvas
        self.plugin = plugin
        self.saveButton.clicked.connect(self.saveconfig)

    def initConfig(self):
        self.sideDistInt = self.settings.value('PisteCreator/calculation_variable/side_distance', 6)
        self.sideDistSpinBox.setValue(int(self.sideDistInt))

        self.aslopeInt = self.settings.value('PisteCreator/graphical_visualisation/tolerated_a_slope', 10)
        self.toleratedASlopeSpinBox.setValue(int(self.aslopeInt))

        self.cslopeInt = self.settings.value('PisteCreator/graphical_visualisation/tolerated_c_slope', 4)
        self.toleratedCSlopeSpinBox.setValue(int(self.cslopeInt))

        self.lengthInt = self.settings.value('PisteCreator/graphical_visualisation/max_length', 50)
        self.maxLengthSpinBox.setValue(int(self.lengthInt))

        self.lengthBool = self.settings.value('PisteCreator/graphical_visualisation/max_length_hold', False)
        self.maxLengthCheckBox.setChecked(bool(self.lengthBool))

        self.swathInt = self.settings.value('PisteCreator/graphical_visualisation/swath_distance', 30)
        self.swathDistSpinBox.setValue(int(self.swathInt))

        self.swathBool = self.settings.value('PisteCreator/graphical_visualisation/swath_display', True)
        self.swathDistCheckBox.setChecked(bool(self.swathBool))
        
        self.interpolBool = self.settings.value('PisteCreator/calculation_variable/interpolate_act', True)
        self.interpolCheckBox.setChecked(bool(self.interpolBool))

        self.t_color = QColor(self.settings.value('PisteCreator/graphical_visualisation/t_color', '#00d003'
            ))
        self.f_color = QColor(self.settings.value('PisteCreator/graphical_visualisation/f_color', '#ff0000'
            ))
        self.tl_color = QColor(self.settings.value('PisteCreator/graphical_visualisation/tl_color', '#236433'
            ))
        self.fl_color = QColor(self.settings.value('PisteCreator/graphical_visualisation/fl_color', '#b80000'
            ))
        self.b_color = QColor(self.settings.value('PisteCreator/graphical_visualisation/b_color', '#0fff33'
            ))
        self.a_color = QColor(self.settings.value('PisteCreator/graphical_visualisation/a_color', '#48b0d2'
            ))
        self.T_ColorButton.setColor(self.t_color)
        self.F_ColorButton.setColor(self.f_color)
        self.TL_ColorButton.setColor(self.tl_color)
        self.FL_ColorButton.setColor(self.fl_color)
        self.B_ColorButton.setColor(self.b_color)
        self.A_ColorButton.setColor(self.a_color)

    def saveconfig(self):
        # self.checkChanges()
        self.sideDistInt = self.sideDistSpinBox.value()
        self.aslopeInt = self.toleratedASlopeSpinBox.value()
        self.cslopeInt = self.toleratedCSlopeSpinBox.value()
        self.lengthInt = self.maxLengthSpinBox.value()
        self.lengthBool  = self.maxLengthCheckBox.isChecked()
        self.swathInt = self.swathDistSpinBox.value()
        self.swathBool = self.swathDistCheckBox.isChecked()
        self.interpolBool = self.interpolCheckBox.isChecked()
        self.t_color = self.T_ColorButton.color().name()
        self.f_color = self.F_ColorButton.color().name()
        self.tl_color = self.TL_ColorButton.color().name()
        self.fl_color= self.FL_ColorButton.color().name()
        self.a_color = self.A_ColorButton.color().name()
        self.b_color = self.B_ColorButton.color().name()

        self.settings.setValue('PisteCreator/calculation_variable/side_distance',
            self.sideDistSpinBox.value())
        self.settings.setValue('PisteCreator/graphical_visualisation/tolerated_a_slope',
            self.toleratedASlopeSpinBox.value())
        self.settings.setValue('PisteCreator/graphical_visualisation/tolerated_c_slope',
            self.toleratedCSlopeSpinBox.value())
        self.settings.setValue('PisteCreator/graphical_visualisation/max_length',
            self.maxLengthSpinBox.value())
        self.settings.setValue('PisteCreator/graphical_visualisation/max_length_hold',
            self.maxLengthCheckBox.isChecked())
        self.settings.setValue('PisteCreator/graphical_visualisation/swath_distance',
            self.swathDistSpinBox.value())
        self.settings.setValue('PisteCreator/graphical_visualisation/swath_display',
            self.swathDistCheckBox.isChecked())
        self.settings.setValue('PisteCreator/calculation_variable/interpolate_act',
            self.interpolCheckBox.isChecked())
        self.settings.setValue('PisteCreator/graphical_visualisation/t_color',
            self.T_ColorButton.color().name())
        self.settings.setValue('PisteCreator/graphical_visualisation/f_color',
            self.F_ColorButton.color().name())
        self.settings.setValue('PisteCreator/graphical_visualisation/tl_color',
            self.TL_ColorButton.color().name())
        self.settings.setValue('PisteCreator/graphical_visualisation/fl_color',
            self.FL_ColorButton.color().name())
        self.settings.setValue('PisteCreator/graphical_visualisation/b_color',
            self.B_ColorButton.color().name())
        self.settings.setValue('PisteCreator/graphical_visualisation/a_color',
            self.A_ColorButton.color().name())

        try:
            if self.canvas.mapTool().map_tool_name == 'SlopeMapTool':
                self.plugin.PisteCreatorTool.configChange(
                    self.sideDistInt,self.aslopeInt,self.cslopeInt,self.lengthInt,
                    self.lengthBool,self.swathInt,self.swathBool,self.interpolBool,
                    self.t_color,self.f_color,self.tl_color,self.fl_color,
                    self.b_color,self.a_color)
        except AttributeError:
            pass
        self.close()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
