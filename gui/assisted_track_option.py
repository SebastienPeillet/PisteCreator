# -*- coding: utf-8 -*-
"""
/***************************************************************************
 assisted_track_option
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

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.PyQt.QtCore import pyqtSignal


class AssistedTrackOption(QDockWidget):

    closingPlugin = pyqtSignal()
    keyPressed = QtCore.pyqtSignal()

    def __init__(self, dock, parent=None):
        """Constructor."""
        super(AssistedTrackOption, self).__init__(parent)
        uic.loadUi(
            os.path.join(os.path.dirname(__file__), "assisted_track_option.ui"), self
        )

        self.key = None

    def keyPressEvent(self, e):
        super(AssistedTrackOption, self).keyPressEvent(e)
        self.key = e
        self.keyPressed.emit()

    def closeEvent(self, event):
        """Clove event"""
        self.closingPlugin.emit()
        event.accept()
