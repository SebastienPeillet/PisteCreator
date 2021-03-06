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

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'PisteCreator_dockwidget_base.ui'))


class PisteCreatorDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(PisteCreatorDockWidget, self).__init__(parent)

        self.setupUi(self)

    def closeEvent(self, event):
        """Clove event"""
        self.closingPlugin.emit()
        event.accept()
