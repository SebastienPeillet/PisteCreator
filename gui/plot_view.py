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
import bisect
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QSizeF, QRectF, QSize, QSettings
from PyQt5.QtGui import QIcon, QColor, QPen, QBrush, QFont
from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsWidget,
    QWidget,
    QAction,
    QToolBar,
    QLabel,
    QStatusBar,
    QVBoxLayout,
)
from qgis.core import (QgsFeatureRenderer,
                      QgsMapToPixel,
                      QgsRenderContext,
                      QgsGeometry,
                      QgsFields,
                      QgsFeature,
                      QgsRectangle)

POINT_RENDERER = 0
LINE_RENDERER = 1
POLYGON_RENDERER = 2

class Axes(QGraphicsWidget):
    def __init__(self, vertical=False, size=QSizeF(200, 100), parent=None):
        super().__init__(parent)
        self.__vertical = vertical
        self.__item_size = size
        self.__font = QFont()
        self.__font.setPointSize(9)
        self.__min = 0
        self.__max = 100

    def set_min_x(self, x):
        self.__min = x

    def set_max_x(self, x):
        self.__max = x

    def boundingRect(self):
        """ Return bounding rectangle

        :return: bounding rectangle
        :rtype: QRectF
        """
        return QRectF(0, 0, self.__item_size.width(), self.__item_size.height())

    def height(self):
        """ Return plot height

        :return: height
        :rtype: float
        """
        return self.__item_size.height()

    def set_height(self, height):
        """ Set plot height

        :param height: height
        :type height: float
        """
        self.__item_size.setHeight(height)

    def width(self):
        """ Return plot width

        :return: width
        :rtype: float
        """
        return self.__item_size.width()

    def set_width(self, width):
        """ Set plot width

        :param width: width
        :type width: float
        """
        self.__item_size.setWidth(width)

    def is_vertical(self):
        return self.__vertical

    def paint(self, painter, option, widget):
        """ Paint plot item, heritated from QGraphicsItem

        :param painter: QPainter
        :type painter: QPainter
        :param option: QStyleOptionGraphicsItem
        :type option: QStyleOptionGraphicsItem
        :param widget: QWidget
        :type widget: QWidget
        """
        old_pen = painter.pen()
        old_brush = painter.brush()
        p = QPen()
        b = QBrush()
        p.setColor(QColor("#000000"))
        p.setWidth(1)
        painter.setFont(self.__font)
        fm = painter.fontMetrics()
        width, height = int(self.__item_size.width()), int(self.__item_size.height())
        if self.__vertical:
            painter.translate(height / 2, width / 2)
            painter.rotate(-90.0)
            painter.translate(-width / 2, -height / 2)
            offset = 35
            axe_height = width-offset
            axe_x = 50
            painter.drawLine(offset, axe_x, axe_height+10, axe_x)
            painter.drawLine(axe_height+5, axe_x-3, axe_height+10,axe_x)
            painter.drawLine(axe_height+10, axe_x, axe_height+5,axe_x+3)

            pixels_per_tick = self.__max / axe_height
            mm = 0
            while mm <= self.__max:
                y = mm / self.__max * (axe_height-offset) + offset

                tick_size = 0
                if mm == 0:
                    tick_size = 10
                elif mm % 20 == 0 and pixels_per_tick < 1:
                    tick_size = 10
                elif mm % 10 == 0 and pixels_per_tick < 0.5:
                    tick_size = 5
                elif pixels_per_tick < 0.25:
                    tick_size = 2
                elif mm %50 == 0 and pixels_per_tick > 1:
                    tick_size = 10

                if tick_size > 0:
                    # painter.drawLine(0, y, tick_size, y)
                    painter.drawLine(y, axe_x - tick_size, y, axe_x)
                    if tick_size == 10:
                        s = str(mm)
                        x = (axe_x - tick_size - 2)
                        painter.drawText(y - fm.width(s) / 2, x, s)
                    elif pixels_per_tick < 0.25 and tick_size == 5:
                        s = str(mm)
                        x = (axe_x - tick_size - 2)
                        painter.drawText(y - fm.width(s) / 2, x, s)
                mm += 5


            # add "..." if needed
            title = fm.elidedText('Slope percent', Qt.ElideRight, width)
            w1 = int((width - fm.width(title)) / 2)
            y = int(20)
            painter.drawText(w1, y, title)
        else :
            offset = 50
            axe_width = width-offset
            axe_y = 0
            painter.drawLine(0, axe_y, axe_width+10, axe_y)
            painter.drawLine(axe_width+5, axe_y-3, axe_width+10,axe_y)
            painter.drawLine(axe_width+10, axe_y, axe_width+5,axe_y+3)

            length = self.__max - self.__min
            step = int(float('1e'+str(len(str(length/10).split('.')[0]))))/10
            pixels_per_tick = axe_width/int(length/step)
            mm = self.__min
            while mm <= self.__max :
                y = mm / length * (axe_width)

                tick_size = 0
                if mm == self.__min:
                    tick_size = 10
                elif mm % (1*step) == 0 and pixels_per_tick > fm.width(str(step)):
                    tick_size = 5
                elif mm % (2*step) == 0 and pixels_per_tick > fm.width(str(step))/2:
                    tick_size = 10
                elif mm % (5*step) == 0 and pixels_per_tick < fm.width(str(step))/2 and pixels_per_tick > fm.width(str(step))/5:
                    tick_size = 10
                elif mm % (10*step) == 0:
                    tick_size = 10

                if tick_size > 0:
                    # painter.drawLine(0, y, tick_size, y)
                    painter.drawLine(y, axe_y + tick_size, y, axe_y)
                    if tick_size == 10:
                        s = str(int(mm))
                        x = (axe_y + tick_size + fm.ascent() + 2)
                        painter.drawText(y - fm.width(s) / 2, x, s)
                    elif pixels_per_tick > fm.width(str(step)) and tick_size == 5:
                        s = str(int(mm))
                        x = (axe_y + tick_size + fm.ascent() + 2)
                        painter.drawText(y - fm.width(s) / 2, x, s)
                if mm == self.__min:
                    mm = int(mm/step)*step
                mm += step            

            # add "..." if needed
            title = fm.elidedText('Length', Qt.ElideRight, width)
            w1 = int((width - offset - fm.width(title)) / 2)
            y = int(33)
            painter.drawText(w1, y, title)


        painter.setBrush(old_brush)
        painter.setPen(old_pen)

    def mouseMoveEvent(self, event):
        """ On mouse move event

        :param event: event
        :type event: QEvent
        """
        pos = event.scenePos()
        
class SlopePlot(QGraphicsWidget):
    def __init__(self, size=QSizeF(400, 200), render_type=LINE_RENDERER, parent=None):
        QGraphicsWidget.__init__(self, parent)
        self.__item_size = size
        self.__x_values = []
        self.__a_values = []
        self.__cl_values = []
        self.__cr_values = []
        if not self.__x_values :
            self.set_data_window(QRectF(0,
                                 0,
                                 100,
                                 100
                                ))
        else:
            self.set_data_window(QRectF(0,
                                 0,
                                 max(self.__x_values),
                                 max(self.__a_values + self.__cl_values + self.__cr_values)
                                ))

        self.__render_type = render_type
        self.__default_a_renderers = [
            QgsFeatureRenderer.defaultRenderer(POINT_RENDERER),
            QgsFeatureRenderer.defaultRenderer(LINE_RENDERER),
            QgsFeatureRenderer.defaultRenderer(POLYGON_RENDERER),
        ]
        self.__default_c_renderers = [
            QgsFeatureRenderer.defaultRenderer(POINT_RENDERER),
            QgsFeatureRenderer.defaultRenderer(LINE_RENDERER),
            QgsFeatureRenderer.defaultRenderer(POLYGON_RENDERER),
        ]
        symbol = self.__default_a_renderers[1].symbol()
        symbol.setWidth(1.0)
        symbol = self.__default_a_renderers[0].symbol()
        symbol.setSize(5.0)
        symbol = self.__default_a_renderers[2].symbol()
        symbol.symbolLayers()[0].setStrokeWidth(1.0)
        symbol = self.__default_c_renderers[1].symbol()
        symbol.setWidth(1.0)
        symbol = self.__default_c_renderers[0].symbol()
        symbol.setSize(5.0)
        symbol = self.__default_c_renderers[2].symbol()
        symbol.symbolLayers()[0].setStrokeWidth(1.0)

        self.__default_a_renderers[self.__render_type].symbol().setColor(QColor('#ff0000'))
        self.__a_renderer = self.__default_a_renderers[self.__render_type]
        self.__default_c_renderers[self.__render_type].symbol().setColor(QColor('#00ff00'))
        self.__c_renderer = self.__default_c_renderers[self.__render_type]

    def set_data(self, x_values, a_values, cl_values, cr_values):
        settings = QSettings()
        tolerated_a_slope = int(settings.value("PisteCreator/graphical_visualisation/tolerated_a_slope", 10))
        tolerated_c_slope = int(settings.value("PisteCreator/graphical_visualisation/tolerated_c_slope", 10))
        if x_values:
            self.__x_values = x_values
            self.__a_values = a_values
            self.__cl_values = cl_values
            self.__cr_values = cr_values
            self.set_width_x(max(self.__x_values))
            self.set_height_y(max(a_values + cl_values + cr_values + [tolerated_a_slope, tolerated_c_slope])+5)
        else:
            self.__x_values = []
            self.__a_values = []
            self.__cl_values = []
            self.__cr_values = []
            if not self.__x_values :
                self.set_data_window(QRectF(0,
                                     0,
                                     100,
                                     max([tolerated_a_slope, tolerated_c_slope])+5
                                    ))
        

    @staticmethod
    def qgis_render_context(painter, width, height):
        """Return qgis render context"""
        mtp = QgsMapToPixel()
        # the default viewport if centered on 0, 0
        mtp.setParameters(
            1,  # map units per pixel
            int(width / 2),  # map center in geographical units
            int(height / 2),  # map center in geographical units
            int(width),  # output width in pixels
            int(height),  # output height in pixels
            0.0,  # rotation in degrees
        )
        context = QgsRenderContext()
        context.setMapToPixel(mtp)
        context.setPainter(painter)
        return context

    def boundingRect(self):
        """ Return bounding rectangle

        :return: bounding rectangle
        :rtype: QRectF
        """
        return QRectF(0, 0, self.__item_size.width(), self.__item_size.height())

    def height(self):
        """ Return plot height

        :return: height
        :rtype: float
        """
        return self.__item_size.height()

    def set_height(self, height):
        """ Set plot height

        :param height: height
        :type height: float
        """
        self.__item_size.setHeight(height)

    def width(self):
        """ Return plot width

        :return: width
        :rtype: float
        """
        return self.__item_size.width()

    def set_width(self, width):
        """ Set plot width

        :param width: width
        :type width: float
        """
        self.__item_size.setWidth(width)

    def min_x(self):
        """ Return min depth value

        :return: min depth value
        :rtype: float
        """
        if self.__data_rect is None:
            return None
        return self.__data_rect.x()

    def max_x(self):
        """ Return max x value

        :return: max x value
        :rtype: float
        """
        if self.__data_rect is None:
            return None
        return self.__data_rect.x() + self.__data_rect.width()

    def set_min_x(self, min_x):
        """ Set min x value

        :param min_x: min x value
        :type min_x: float
        """
        if self.__data_rect is not None:
            self.__data_rect.setX(min_x)

    def set_width_x(self, max_x):
        """ Set max x value

        :param max_x: max x value
        :type max_x: float
        """
        if self.__data_rect is not None:
            w = max_x - self.__data_rect.x()
            self.__data_rect.setWidth(w)

    def set_min_y(self, min_y):
        """ Set min y value

        :param min_y: min y value
        :type min_y: float
        """
        if self.__data_rect is not None:
            self.__data_rect.setY(min_y)

    def set_height_y(self, max_y):
        """ Set max y value

        :param max_y: max y value
        :type max_y: float
        """
        if self.__data_rect is not None:
            h = max_y - self.__data_rect.y()
            self.__data_rect.setHeight(h)
    

    def set_data_window(self, window):
        """ Set data_window

        :param window: QRectF
        :type windows: QRectF
        """
        self.__data_rect = window

    def data_window(self):
        """ Return data_window

        :return: data_window
        :rtype: QRectF
        """
        return self.__data_rect

    def draw_background(self, painter, outline=True):
        """draw background of the log item

        :param painter: painter
        :type QPainter: QPainter
        :param outline: false if legend item
        :type outline: bool
        """
        old_pen = painter.pen()
        old_brush = painter.brush()
        p = QPen()
        b = QBrush()
        width, height = int(self.boundingRect().width()), int(self.boundingRect().height())
        b.setColor(QColor("#ffffff"))
        b.setStyle(Qt.SolidPattern)
        painter.setBrush(b)
        if outline:
            p.setColor(QColor("#000000"))
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRect(0, 0, width, height)
        else:
            p.setColor(QColor("#ffffff"))
            p.setWidth(0)
            painter.setPen(p)
            painter.drawRect(0, 0, width, height - 1)
        painter.setBrush(old_brush)
        painter.setPen(old_pen)

    def paint(self, painter, option, widget):
        """ Paint plot item, heritated from QGraphicsItem

        :param painter: QPainter
        :type painter: QPainter
        :param option: QStyleOptionGraphicsItem
        :type option: QStyleOptionGraphicsItem
        :param widget: QWidget
        :type widget: QWidget
        """
        # self.draw_background(painter)
        old_pen = painter.pen()
        old_brush = painter.brush()
        settings = QSettings()
        y_offset = 35
        x_offset = 50
        graph_height = self.height()-y_offset
        graph_width = self.width()
        p = QPen()
        b = QBrush()
        p.setColor(QColor('#000000'))
        p.setWidth(1)
        p.setStyle(2)
        painter.setPen(p)
        tolerated_a_slope = int(settings.value("PisteCreator/graphical_visualisation/tolerated_a_slope", 10))
        print('donnee : ', graph_height, self.__data_rect.height())
        painter.drawLine(0,
                         (1-(tolerated_a_slope/self.__data_rect.height()))*self.__item_size.height(),
                         graph_width,
                         (1-(tolerated_a_slope/self.__data_rect.height()))*self.__item_size.height() 
                        )
        if int(settings.value('PisteCreator/calculation_variable/mode', '0')) != 2:
            p.setStyle(3)
            painter.setPen(p)
            tolerated_c_slope = int(settings.value("PisteCreator/graphical_visualisation/tolerated_c_slope", 4))
            painter.drawLine(0,
                             (1-(tolerated_c_slope/self.__data_rect.height()))*self.__item_size.height(),
                             graph_width,
                             (1-(tolerated_c_slope/self.__data_rect.height()))*self.__item_size.height(),
                            )

        painter.setBrush(old_brush)
        painter.setPen(old_pen)

        self.line_rendering(painter,self.__x_values,self.__a_values, self.__a_renderer)
        self.line_rendering(painter,self.__x_values,self.__cr_values, self.__c_renderer)
        self.line_rendering(painter,self.__x_values,self.__cl_values, self.__c_renderer)

    def line_rendering(self, painter, x_values, y_values, renderer, render_type=LINE_RENDERER):
        imin_x = bisect.bisect_left(sorted(x_values), self.__data_rect.x(), hi=len(x_values))

        imax_x = bisect.bisect_right(
            sorted(x_values), self.__data_rect.right(), hi=len(x_values)
        )

        # For lines and polygons, retain also one value before the min and one after the max
        # so that lines do not appear truncated
        # Do this only if we have at least one point to render within out rect
        if imin_x > 0 and imin_x < len(x_values) and x_values[imin_x] >= self.__data_rect.x():
            # FIXME add a test to avoid adding a point too "far away" ?
            imin_x -= 1
        if imax_x < len(x_values) - 1 and x_values[imax_x] <= self.__data_rect.right():
            # FIXME add a test to avoid adding a point too "far away" ?
            imax_x += 1

        x_values_slice = np.array(x_values[imin_x:imax_x])
        y_values_slice = np.array(y_values[imin_x:imax_x])

        if len(x_values_slice) == 0:
            return (None, None)

        # filter points that are not None (nan in numpy arrays)
        n_points = len(x_values_slice)
        if self.__data_rect.width() > 0:
            rw = float(self.__item_size.width()) / self.__data_rect.width()
        else:
            rw = float(self.__item_size.width())
        if self.__data_rect.height() > 0:
            rh = float(self.__item_size.height()) / self.__data_rect.height()
        else:
            rh = float(self.__item_size.height())
        xx = (x_values_slice - self.__data_rect.x()) * rw
        yy = (y_values_slice - self.__data_rect.y()) * rh

        self.__rw = rw
        self.__rh = rh

        if render_type == LINE_RENDERER:
            # WKB structure of a linestring
            #
            #   01 : endianness
            #   02 00 00 00 : WKB type (linestring)
            #   nn nn nn nn : number of points (int32)
            # Then, for each point:
            #   xx xx xx xx xx xx xx xx : X coordinate (float64)
            #   yy yy yy yy yy yy yy yy : Y coordinate (float64)

            wkb = np.zeros(8 * 2 * n_points + 9, dtype="uint8")
            wkb[0] = 1  # wkb endianness
            wkb[1] = 2  # linestring
            size_view = np.ndarray(buffer=wkb, dtype="int32", offset=5, shape=(1,))
            size_view[0] = n_points
            coords_view = np.ndarray(buffer=wkb, dtype="float64", offset=9, shape=(n_points, 2))
            coords_view[:, 0] = xx[:]
            coords_view[:, 1] = yy[:]
        elif render_type == POINT_RENDERER:
            # WKB structure of a multipoint
            #
            #   01 : endianness
            #   04 00 00 00 : WKB type (multipoint)
            #   nn nn nn nn : number of points (int32)
            # Then, for each point:
            #   01 : endianness
            #   01 00 00 00 : WKB type (point)
            #   xx xx xx xx xx xx xx xx : X coordinate (float64)
            #   yy yy yy yy yy yy yy yy : Y coordinate (float64)

            wkb = np.zeros((8 * 2 + 5) * n_points + 9, dtype="uint8")
            wkb[0] = 1  # wkb endianness
            wkb[1] = 4  # multipoint
            size_view = np.ndarray(buffer=wkb, dtype="int32", offset=5, shape=(1,))
            size_view[0] = n_points
            coords_view = np.ndarray(
                buffer=wkb, dtype="float64", offset=9 + 5, shape=(n_points, 2), strides=(16 + 5, 8)
            )
            coords_view[:, 0] = xx[:]
            coords_view[:, 1] = yy[:]
            # header of each point
            h_view = np.ndarray(
                buffer=wkb, dtype="uint8", offset=9, shape=(n_points, 2), strides=(16 + 5, 1)
            )
            h_view[:, 0] = 1  # endianness
            h_view[:, 1] = 1  # point
        elif render_type == POLYGON_RENDERER:
            # WKB structure of a polygon
            #
            #   01 : endianness
            #   03 00 00 00 : WKB type (polygon)
            #   01 00 00 00 : Number of rings (always 1 here)
            #   nn nn nn nn : number of points (int32)
            # Then, for each point:
            #   xx xx xx xx xx xx xx xx : X coordinate (float64)
            #   yy yy yy yy yy yy yy yy : Y coordinate (float64)
            #
            # We add two additional points to close the polygon

            wkb = np.zeros(8 * 2 * (n_points + 2) + 9 + 4, dtype="uint8")
            wkb[0] = 1  # wkb endianness
            wkb[1] = 3  # polygon
            wkb[5] = 1  # number of rings
            size_view = np.ndarray(buffer=wkb, dtype="int32", offset=9, shape=(1,))
            size_view[0] = n_points + 2
            coords_view = np.ndarray(buffer=wkb, dtype="float64", offset=9 + 4, shape=(n_points, 2))
            coords_view[:, 0] = xx[:]
            coords_view[:, 1] = yy[:]
            # two extra points
            extra_coords = np.ndarray(
                buffer=wkb, dtype="float64", offset=8 * 2 * n_points + 9 + 4, shape=(2, 2)
            )
            if (
                self.__x_orientation == ORIENTATION_LEFT_TO_RIGHT
                and self.__y_orientation == ORIENTATION_UPWARD
            ):
                extra_coords[0, 0] = coords_view[-1, 0]
                extra_coords[0, 1] = 0.0
                extra_coords[1, 0] = coords_view[0, 0]
                extra_coords[1, 1] = 0.0
            elif (
                self.__x_orientation == ORIENTATION_DOWNWARD
                and self.__y_orientation == ORIENTATION_LEFT_TO_RIGHT
            ):
                extra_coords[0, 0] = 0.0
                extra_coords[0, 1] = coords_view[-1, 1]
                extra_coords[1, 0] = 0.0
                extra_coords[1, 1] = coords_view[0, 1]

        # build a geometry from the WKB
        # since numpy arrays have buffer protocol, sip is able to read it
        geom = QgsGeometry()
        geom.fromWkb(wkb.tobytes())

        painter.setClipRect(0, 0, int(self.__item_size.width()), int(self.__item_size.height()))

        fields = QgsFields()
        # fields.append(QgsField("", QVariant.String))
        feature = QgsFeature(fields, 1)
        feature.setGeometry(geom)

        context = self.qgis_render_context(painter, self.__item_size.width(), self.__item_size.height())
        context.setExtent(QgsRectangle(0, 1, self.__item_size.width(), self.__item_size.height()))

        renderer.startRender(context, fields)
        renderer.renderFeature(feature, context)
        renderer.stopRender(context)

class MyScene(QGraphicsScene):
    """Qgeologis Scene"""
    plot_edited = pyqtSignal()

    def __init__(self, x, y, w, h):
        """MyScene is the general scene in which items are displayed

        :param x: x origin
        :type x: int
        :param y: y origin
        :type y: int
        :param w: width
        :type w: int
        :param h: height
        :type h: int
        """
        super().__init__(x, y, w, h)
        self.sceneRectChanged.connect(self.resizeItems)

    def resizeItems(self):
        for item in self.items():
            if isinstance(item, SlopePlot):
                item.set_height(self.height()-35)
                item.set_width(self.width())
            if isinstance(item, Axes):
                if item.is_vertical():
                    item.set_width(self.height())
                else :
                    item.set_width(self.width()-50)
        self.update()

    def mouseMoveEvent(self, event):
        """Pass the event to the underlying item

        :param event: event to pass
        :type event: QEvent
        """
        for item in list(self.items()):
            r = item.boundingRect()
            r.translate(item.pos())
            if r.contains(event.scenePos()):
                return item.mouseMoveEvent(event)
        return QGraphicsScene.mouseMoveEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        """Pass the event to the underlying item

        :param event: event to pass
        :type event: QEvent
        """
        for item in list(self.items()):
            r = item.boundingRect()
            r.translate(item.pos())
            if r.contains(event.scenePos()) and isinstance(item, LegendItem):
                return self.plot_edited.emit()
        return QGraphicsScene.mouseDoubleClickEvent(self, event)

class PlotGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        """ View handles user interaction, like resize, mouse etc

        :param scene: MyScene, heritated from QGraphicScene
        :type scene: MyScene
        :param parent: parent
        :type parent: QObjet
        """
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

    def resizeEvent(self, event):
        """ Triggered on windows resize, recenter view

        :param event: QEvent
        :type event: QEvent
        """
        QGraphicsView.resizeEvent(self, event)
        # by default, the rect is centered on 0,0,
        # we prefer to have 0,0 in the upper left corner
        rect = QRectF(0, 0, event.size().width(), event.size().height()-1)
        self.scene().setSceneRect(rect)
        self.scene().sceneRectChanged.emit(rect)

class PlotView(QWidget):
    """Plot view widget"""

    centerSceneOnScale = pyqtSignal()

    def __init__(
        self,
        parent=None,
    ):
        """Plot Widget inserted into main dialog.
        :param parent: parent
        :type parent: QObject

        """
        QWidget.__init__(self, parent)
        self._scene = MyScene(0, 0, 400, 250)
        self.__view = PlotGraphicsView(self._scene)
        self.__view.setMinimumHeight(200)
        self.centerSceneOnScale.connect(self.center_scene_on_scale)
        self._scene.sceneRectChanged.connect(self.on_rect_changed)
        box = QVBoxLayout()
        box.addWidget(self.__view)
        plot_v_axe = Axes(True)
        plot_v_axe.setGeometry(0, 0, 100, plot_v_axe.height())
        plot_h_axe = Axes(False, QSize(400,30))
        plot_h_axe.setGeometry(50, self._scene.height()-35, self._scene.width()-50, 35)
        plot_item = SlopePlot()
        plot_item.setGeometry(50,35,plot_item.width()-100,plot_item.height()-70)
        self._scene.addItem(plot_item)
        self._scene.addItem(plot_v_axe)
        self._scene.addItem(plot_h_axe)
        self.setLayout(box)
        self.centerSceneOnScale.emit()
        # self.on_geom_update([0,200],[10,20],[4,3],[6,7])
        self.on_geom_update([],[],[],[])

    def center_scene_on_scale(self):
        """ For time series, if logs scene is too high for windows,
        focus on the bottom to see the scale
        """
        self.__view.centerOn(
            self._scene.sceneRect().width(),
            self._scene.sceneRect().height() - self.__view.height() / 2 - 1,
        )

    def on_rect_changed(self, rect):
        """Triggered when the widget is resized

        :param rect: Rectangle for scene display
        :type rect: QRect
        """
        for item in self._scene.items():
            if isinstance(item, SlopePlot):
                item.set_width(rect.width()-100)
                item.set_height(rect.height()-70)
            if isinstance(item, Axes):
                if not item.is_vertical():
                    item.setGeometry(50, self._scene.height()-35, self._scene.width()-50, 35)
        self.centerSceneOnScale.emit()

    def on_geom_update(self, x_values, a_values, cl_values, cr_values):
        settings = QSettings()
        tolerated_a_slope = int(settings.value("PisteCreator/graphical_visualisation/tolerated_a_slope", 10))
        tolerated_c_slope = int(settings.value("PisteCreator/graphical_visualisation/tolerated_c_slope", 10))
        for item in self._scene.items():
            if isinstance(item, SlopePlot):
                item.set_data(x_values, a_values, cl_values, cr_values)
            if isinstance(item, Axes):
                if item.is_vertical():
                    if not x_values:
                        item.set_min_x(0)
                        item.set_max_x(max([tolerated_c_slope, tolerated_a_slope])+5)
                    else:
                        item.set_min_x(0)
                        item.set_max_x(max(a_values + cl_values + cr_values + [tolerated_c_slope, tolerated_a_slope])+5)
                else :
                    if not x_values:
                        item.set_min_x(0)
                        item.set_max_x(100)
                    else:
                        item.set_max_x(max(x_values))

        self._scene.update()