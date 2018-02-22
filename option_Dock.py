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

import os

from PyQt4.QtGui import QColor
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from qgis.gui import QgsColorButton
import ConfigParser

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Option_dock.ui'))


class GrumpyConfigParser(ConfigParser.ConfigParser):
    """Virtually identical to the original method,
    but delimit keys and values with '=' instead of ' = '"""
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

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return list(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

class OptionDock(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, plugin, graph_widget, canvas, parent=None):
        """Constructor."""
        super(OptionDock, self).__init__(parent)
        self.setupUi(self)
        self.ConfigParser = None
        self.initPars()
        self.graph_widget = graph_widget
        self.PisteCreatorTool = plugin.PisteCreatorTool
        self.canvas = canvas
        self.plugin = plugin
        self.saveButton.clicked.connect(self.saveconfig)

    def initPars(self):
        self.ConfigParser = GrumpyConfigParser()
        self.ConfigParser.optionxform = str
        configFilePath = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'option.cfg')
        self.ConfigParser.read(configFilePath)

        self.sideDistInt = self.ConfigParser.getint('calculation_variable', 'side_distance')
        self.sideDistSpinBox.setValue(self.sideDistInt)

        self.aslopeInt = self.ConfigParser.getint('graphical_visualisation', 'tolerated_a_slope')
        self.toleratedASlopeSpinBox.setValue(self.aslopeInt)

        self.cslopeInt = self.ConfigParser.getint('graphical_visualisation', 'tolerated_c_slope')
        self.toleratedCSlopeSpinBox.setValue(self.cslopeInt)

        self.lengthInt = self.ConfigParser.getint('graphical_visualisation', 'max_length')
        self.maxLengthSpinBox.setValue(self.lengthInt)

        self.lengthBool = self.ConfigParser.getboolean('graphical_visualisation', 'max_length_hold')
        self.maxLengthCheckBox.setChecked(self.lengthBool)

        self.swathInt = self.ConfigParser.getint('graphical_visualisation', 'swath_distance')
        self.swathDistSpinBox.setValue(self.swathInt)

        self.swathBool = self.ConfigParser.getboolean('graphical_visualisation', 'swath_display')
        self.swathDistCheckBox.setChecked(self.swathBool)
        
        self.interpolBool = self.ConfigParser.getboolean('calculation_variable', 'interpolate_act')
        self.interpolCheckBox.setChecked(self.interpolBool)

        self.t_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 't_color'
            ))
        self.f_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'f_color'
            ))
        self.tl_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'tl_color'
            ))
        self.fl_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'fl_color'
            ))
        self.b_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'b_color'
            ))
        self.a_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'a_color'
            ))
        self.T_ColorButton.setColor(self.t_color)
        self.F_ColorButton.setColor(self.f_color)
        self.TL_ColorButton.setColor(self.tl_color)
        self.FL_ColorButton.setColor(self.fl_color)
        self.B_ColorButton.setColor(self.b_color)
        self.A_ColorButton.setColor(self.a_color)

    # def checkChanges(self):
    #     if self.sideDistSpinBox.value() != self.sideDistInt:
    #         emit()
    #     elif self.toleratedASlopeSpinBox.value() != self.aslopeInt:
    #         emit()
    #     elif self.self.toleratedCSlopeSpinBox.value() != self.cslopeInt:
    #         emit()
    #     elif self.maxLengthSpinBox.value() != self.lengthInt:
    #         emit()
    #     elif self.maxLengthCheckBox.isChecked() != self.lengthBool:
    #         emit()
    #     elif self.swathDistSpinBox.value() != self.swathInt:
    #         emit()
    #     elif self.swathDistCheckBox.isChecked() != self.swathBool:
    #         emit()
    #     elif self.interpolCheckBox.isChecked() != self.interpolBool:
    #         emit()

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

        self.ConfigParser.set(
            'calculation_variable',
            'side_distance',
            self.sideDistSpinBox.value()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'tolerated_a_slope',
            self.toleratedASlopeSpinBox.value()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'tolerated_c_slope',
            
            self.toleratedCSlopeSpinBox.value()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'max_length',
            self.maxLengthSpinBox.value()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'max_length_hold',
            self.maxLengthCheckBox.isChecked()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'swath_distance',
            self.swathDistSpinBox.value()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'swath_display',
            self.swathDistCheckBox.isChecked()
        )
        self.ConfigParser.set(
            'calculation_variable',
            'interpolate_act',
            self.interpolCheckBox.isChecked()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            't_color',
            self.T_ColorButton.color().name()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'f_color',
            self.F_ColorButton.color().name()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'tl_color',
            self.TL_ColorButton.color().name()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'fl_color',
            self.FL_ColorButton.color().name()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'b_color',
            self.B_ColorButton.color().name()
        )
        self.ConfigParser.set(
            'graphical_visualisation',
            'a_color',
            self.A_ColorButton.color().name()
        )

        with open(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), 'option.cfg'
            ),
            'wb'
        ) as configfile:
            self.ConfigParser.write(configfile)
        self.graph_widget.initPars()
        self.graph_widget.plot([], [], [], [])
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
