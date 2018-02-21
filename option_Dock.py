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
        self.canvas = canvas
        self.plugin = plugin
        self.saveButton.clicked.connect(self.saveconfig)

    def initPars(self):
        self.ConfigParser = GrumpyConfigParser()
        self.ConfigParser.optionxform = str
        configFilePath = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'option.cfg')
        self.ConfigParser.read(configFilePath)
        self.sideDistSpinBox.setValue(
            self.ConfigParser.getint(
                'calculation_variable', 'side_distance'
            )
        )
        self.toleratedASlopeSpinBox.setValue(
            self.ConfigParser.getint(
                'graphical_visualisation', 'tolerated_a_slope'
                )
        )
        self.toleratedCSlopeSpinBox.setValue(
            self.ConfigParser.getint(
                'graphical_visualisation', 'tolerated_c_slope'
            )
        )
        self.maxLengthSpinBox.setValue(
            self.ConfigParser.getint(
                'graphical_visualisation', 'max_length'
            )
        )
        self.maxLengthCheckBox.setChecked(
            self.ConfigParser.getboolean(
                'graphical_visualisation', 'max_length_hold'
            )
        )
        self.swathDistSpinBox.setValue(
            self.ConfigParser.getint(
                'graphical_visualisation', 'swath_distance'
            )
        )
        self.swathDistCheckBox.setChecked(
            self.ConfigParser.getboolean(
                'graphical_visualisation', 'swath_display'
            )
        )
        self.interpolCheckBox.setChecked(
            self.ConfigParser.getboolean(
                'calculation_variable', 'interpolate_act'
            )
        )
        t_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 't_color'
            ))
        f_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'f_color'
            ))
        tl_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'tl_color'
            ))
        fl_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'fl_color'
            ))
        b_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'b_color'
            ))
        a_color = QColor(self.ConfigParser.get(
                'graphical_visualisation', 'a_color'
            ))
        self.T_ColorButton.setColor(t_color)
        self.F_ColorButton.setColor(f_color)
        self.TL_ColorButton.setColor(tl_color)
        self.FL_ColorButton.setColor(fl_color)
        self.B_ColorButton.setColor(b_color)
        self.A_ColorButton.setColor(a_color)

    def saveconfig(self):
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
                self.plugin.slopeCalc()
        except AttributeError:
            pass
        self.close()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
