# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreatorDockWidget_OptionDock
                                 Option dock for Qgis plugins
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
import ConfigParser

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Option_dock.ui'))


class GrumpyConfigParser(ConfigParser.ConfigParser):
  """Virtually identical to the original method, but delimit keys and values with '=' instead of ' = '"""
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

                    # This is the important departure from ConfigParser for what you are looking for
                    key = "=".join((key, str(value).replace('\n', '\n\t')))

                fp.write("%s\n" % (key))
        fp.write("\n")


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
        
    def initPars(self) :
        self.ConfigParser = GrumpyConfigParser()
        self.ConfigParser.optionxform = str
        configFilePath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'option.cfg')
        self.ConfigParser.read(configFilePath)
        self.sideDistSpinBox.setValue(self.ConfigParser.getint('calculation_variable', 'side_distance'))
        self.toleratedASlopeSpinBox.setValue(self.ConfigParser.getint('graphical_visualisation', 'tolerated_a_slope'))
        self.toleratedCSlopeSpinBox.setValue(self.ConfigParser.getint('graphical_visualisation', 'tolerated_c_slope'))
        self.maxLengthSpinBox.setValue(self.ConfigParser.getint('graphical_visualisation', 'max_length'))
        self.swathDistSpinBox.setValue(self.ConfigParser.getint('graphical_visualisation', 'swath_distance'))
            
    def saveconfig(self) :
        self.ConfigParser.set('calculation_variable', 'side_distance', self.sideDistSpinBox.value())
        self.ConfigParser.set('graphical_visualisation', 'tolerated_a_slope', self.toleratedASlopeSpinBox.value())
        self.ConfigParser.set('graphical_visualisation', 'tolerated_c_slope', self.toleratedCSlopeSpinBox.value())
        self.ConfigParser.set('graphical_visualisation', 'max_length', self.maxLengthSpinBox.value())
        self.ConfigParser.set('graphical_visualisation', 'swath_distance', self.swathDistSpinBox.value())
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'option.cfg'),'wb') as configfile:
            self.ConfigParser.write(configfile)
        self.graph_widget.initPars()
        self.graph_widget.plot([],[],[],[])
        try :
            if self.canvas.mapTool().map_tool_name == 'SlopeMapTool' :
                self.plugin.slopeCalc()
        except AttributeError :
            pass
        self.close()


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()