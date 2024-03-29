# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreator
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QFileInfo

from qgis.PyQt.QtWidgets import (
    QAction,
    QGraphicsView,
    QGraphicsScene,
    QToolBar,
    QWidget,
)

from qgis.PyQt.QtGui import QIcon

from qgis.gui import QgsMapToolZoom, QgsMapToolIdentify

from qgis.core import QgsRasterLayer, QgsGeometry, QgsProject

from .log import logger

# Import the code for the DockWidget
from .gui.PisteCreator_dockwidget import PisteCreatorDockWidget


class PisteCreator(QWidget):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        super().__init__(None)
        self.iface = iface
        self.canvas = iface.mapCanvas()

        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            os.path.dirname(__file__), "i18n", "PisteCreator_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = None
        self.toolbar = None

        self.pluginIsActive = False
        self.dockwidget = None
        self.PisteCreatorTool = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("PisteCreator", message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(u"&PisteCreator", action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        logger.notice("** INIT PisteCreator")

        self.toolbar = QToolBar(u"PisteCreator")
        self.toolbar.setObjectName(u"PisteCreator")

        action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icon.png")),
            self.tr("PisteCreator"),
            self.iface.mainWindow(),
        )
        action.triggered.connect(self.run)
        self.toolbar.addAction(action)

        self.iface.addToolBar(self.toolbar)
        self.dockwidget = None
        self.canvas.mapToolSet.connect(self.cleanStop)

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        logger.notice("** CLOSING PisteCreator")

        # disconnects
        self.cleanStop()

        self.dockwidget = None
        self.pluginIsActive = False
        self.iface.actionPan().trigger()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        logger.notice("** UNLOAD PisteCreator")

        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&PisteCreator"), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        if self.toolbar is not None:
            self.toolbar.setParent(None)
            self.toolbar = None
        if self.dockwidget is not None:
            self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
            self.iface.removeDockWidget(self.dockwidget)
            self.onClosePlugin()

    # --------------------------------------------------------------------------
    # PisteCreator function

    def cleanStop(self):
        if self.canvas.mapTool() != None:
            if (
                self.PisteCreatorTool != None
                and self.canvas.mapTool().toolName() != "SlopeMapTool"
                and self.canvas.mapTool().toolName() != "SelectMapTool"
            ):
                self.PisteCreatorTool.deactivate()
                self.PisteCreatorTool = None
                self.iface.actionPan().trigger()

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            logger.notice("** STARTING PisteCreator")

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = PisteCreatorDockWidget(self, self.iface)
                self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
                self.dockwidget.closingPlugin.connect(self.onClosePlugin)
        elif self.dockwidget:
            self.pluginIsActive = False
            self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
            self.iface.removeDockWidget(self.dockwidget)
            self.dockwidget = None
