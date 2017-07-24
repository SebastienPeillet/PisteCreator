# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PisteCreator
                                 A QGIS plugin
 ONF UI plugins to create tracks
                              -------------------
        begin                : 2017-04-24
        git sha              : 2017-06-20:11
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QFileInfo
from PyQt4.QtGui import QAction, QIcon, QFileDialog
from qgis.gui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from PisteCreator_dockwidget import PisteCreatorDockWidget
import os.path

from Utils import *
    
class PisteCreator:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.vect_list = []
        self.rast_list = []

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PisteCreator_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&PisteCreator')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PisteCreator')
        self.toolbar.setObjectName(u'PisteCreator')

        #print "** INITIALIZING PisteCreator"

        self.pluginIsActive = False
        self.dockwidget = None


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
        return QCoreApplication.translate('PisteCreator', message)


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
        parent=None):
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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/PisteCreator/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'PisteCreator'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.dockwidget = PisteCreatorDockWidget()
        self.list_vect_layer()
        self.list_rast_layer()
        # self.dockwidget.DEMButton.clicked.connect(self.select_dem_file)
        self.dockwidget.TracksButton.clicked.connect(self.list_vect_layer)
        self.dockwidget.DEMButton.clicked.connect(self.list_rast_layer)
        # self.dockwidget.TracksInput.clicked.connect(self.list_vect_layer)
        # self.dockwidget.DEMInput.clicked.connect(self.list_rast_layer)
        self.dockwidget.EditButton.clicked.connect(self.slopeCalc)


    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING PisteCreator"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD PisteCreator"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&PisteCreator'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
    def select_dem_file(self):
        filename = QFileDialog.getOpenFileName(self.dockwidget, "Select output file ","", '*.tif')
        self.dockwidget.DEMInput.setText(filename)
    
    def list_vect_layer(self):
        #clear list and index
        self.dockwidget.TracksInput.clear()
        self.dockwidget.TracksInput.clearEditText()
        self.vect_list = []
        layers = self.iface.legendInterface().layers()
        layer_list = []
        index = 0
        for layer in layers:
            if layer.type() == 0 :
                layer_list.append(layer.name())
                self.vect_list.append(index)
            index+=1
        self.dockwidget.TracksInput.addItems(layer_list)

    def list_rast_layer(self):
        #clear list and index
        self.dockwidget.DEMInput.clear()
        self.dockwidget.DEMInput.clearEditText()
        self.rast_list = []
        layers = self.iface.legendInterface().layers()
        layer_list = []
        index = 0
        for layer in layers:
            if layer.type() == 1 :
                layer_list.append(layer.name())
                self.rast_list.append(index)
            index+=1
        self.dockwidget.DEMInput.addItems(layer_list)

    def slopeCalc(self):
        #1 Get the vector layer
        layers = self.iface.legendInterface().layers()
        selected_lignes = self.dockwidget.TracksInput.currentIndex()
        linesLayer = layers[self.vect_list[selected_lignes]]
        linesLayer.startEditing()
        #2 Get the raster layer
        selected_lignes = self.dockwidget.DEMInput.currentIndex()
        DEMLayer = layers[self.rast_list[selected_lignes]]
        
        #Load raster layer
        fileName = DEMLayer.publicSource()
        fileInfo = QFileInfo(fileName)
        baseName = fileInfo.baseName()
        #keep raster path for the RasterCalculator operation
        pathRaster = os.path.dirname(fileName)
        dem = QgsRasterLayer(fileName, baseName)
        if not dem.isValid():
            print "Layer failed to load!"
        
        #3 Open edit vector layer
        #4 Activate Maptools
        ct = SlopeMapTool(self.iface,  self.afficheXY, linesLayer, dem);
        self.iface.mapCanvas().setMapTool(ct)
    
    def afficheXY(self,a,b,c,d):
        if a != None :
            self.dockwidget.AlongResult.setText(str(a)+'%')
        if b != None :
            self.dockwidget.LeftCrossResult.setText(str(b)+'%')
        if c != None :
            self.dockwidget.RightCrossResult.setText(str(c)+'%')
        if d != None :
            self.dockwidget.LengthResult.setText(str(d))
    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING PisteCreator"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = PisteCreatorDockWidget()
            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

