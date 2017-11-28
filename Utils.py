# -*- coding: utf-8 -*-
"""
***************************************************************************
 Utils.py
                                A QGIS plugin
 Tools to calculate along and cross slope for road
                            -------------------
        begin				 : 2017-04-24
        last				 : 2017-10-20
        copyright			 : (C) 2017 by Peillet Sebastien
        email				 : peillet.seb@gmail.com
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

from qgis.gui import QgsRubberBand, QgsMapToolIdentify, QgsMapTool
from qgis.core import QgsGeometry, QgsPoint, QgsFeature, QgsRaster, \
    QgsFeatureRequest, QgsSnappingUtils, QgsExpression
from PyQt4.QtGui import QColor
from PyQt4.QtCore import QVariant
import math
import time


class SlopeMapTool(QgsMapTool):
    def __init__(
        self, iface, callback, lines_layer, dem, side_distance,
        tolerated_a_slope, tolerated_c_slope, max_length, swath_distance,
        max_length_hold, swath_display, interpolate_act
    ):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.callback = callback
        self.canvas = iface.mapCanvas()
        self.map_tool_name = 'SlopeMapTool'

        # Config variables
        self.dem = dem
        self.x_res = self.dem.rasterUnitsPerPixelX()
        self.y_res = self.dem.rasterUnitsPerPixelY()
        self.lines_layer = lines_layer
        self.side_distance = side_distance
        self.max_length = max_length
        self.tolerated_a_slope = tolerated_a_slope
        self.tolerated_c_slope = tolerated_c_slope
        self.swath_distance = swath_distance
        self.interpolate_act = interpolate_act

        # Chart variables
        self.line_geom = None
        self.aslope_list = []
        self.c_left_slope_list = []
        self.c_right_slope_list = []

        # Geometric variables
        self.edit = False
        self.point1coord = None
        self.point2coord = None
        self.a_slope = None
        self.c_left_slope = None
        self.c_right_slope = None
        self.length = None
        self.max_length_hold = max_length_hold

        # Rubber variables
        self.swath_display = swath_display
        if self.swath_display is True:
            self.rub_rect = self.rubRectInit()
            self.rub_rect_anchor = self.rubAnchorInit()
            self.rub_rect_anchors = self.rubAnchorsInit()
            self.rub_buff_cursor = self.rubBuffCursorInit()
        self.rub_cursor = self.rubCursorInit()
        self.rub_polyline = self.rubPolylineInit()

        # Snap config
        self.snapper = self.snapperDef()
        return None

    # Event when user move the mouse :
    # it will define a second point and launch slopeCalc function.
    def canvasMoveEvent(self, e):
        """Process the slope calculation when user moves the cursor"""
        self.rub_cursor.removeLastPoint()
        point = self.canvas.getCoordinateTransform().toMapPoint(
            e.pos().x(), e.pos().y()
        )
        if self.max_length_hold is True and self.point1coord is not None:
            pt1 = QgsPoint(self.point1coord)
            x1, y1 = self.point1coord
            pt2 = QgsPoint(point)
            dist = math.sqrt(pt1.sqrDist(pt2))
            if dist >= self.max_length:
                azimuth = pt1.azimuth(pt2)
                xv = math.sin(math.radians(azimuth)) * self.max_length
                yv = math.cos(math.radians(azimuth)) * self.max_length
                x2 = x1 + xv
                y2 = y1 + yv
                self.point2coord = QgsPoint(x2, y2)
            else:
                self.point2coord = point
        else:
            self.point2coord = point
        snap = self.snapper.snapToMap(self.point2coord)
        if snap.isValid() is True:
            x, y = snap.point()
            self.point2coord = QgsPoint(x, y)
        self.rub_cursor.removeLastPoint()
        # if self.rub_cursor.asGeometry().asPoint() == (0,0) :
        self.rub_cursor.addPoint(self.point2coord)
        # self.rub_cursor.movePoint(self.point2coord)

        if self.swath_display is True:
            self.rub_buff_cursor.reset()
            self.rub_buff_cursor.addGeometry(
                QgsGeometry.fromPoint(
                    QgsPoint(
                        self.point2coord[0],
                        self.point2coord[1]))
                .buffer(self.swath_distance, 20), None
            )

        if (
            self.point1coord is not None and self.point2coord is not None
            and self.point1coord != self.point2coord
        ):
            if self.interpolate_act is True:
                self.a_slope, self.c_left_slope, \
                    self.c_right_slope, self.length = \
                    self.slopeCalc(self.point1coord, self.point2coord)
            else:
                self.a_slope, self.c_left_slope, \
                    self.c_right_slope, self.length = \
                    self.slopeCalcWithoutInterpolate(
                        self.point1coord,
                        self.point2coord
                    )
        self.callback(
            self.a_slope, self.c_left_slope, self.c_right_slope, self.length,
            self.line_geom, self.aslope_list, self.c_left_slope_list,
            self.c_right_slope_list, False
        )

        if (
            self.point1coord is not None and self.point2coord is not None
            and self.point1coord != self.point2coord
        ):
            self.rubDisplayUp()

        return None

    # Event when user clicks with the mouse
    def canvasReleaseEvent(self, e):
        """Add new point on the track line.
        A double click or a right click end the track edition."""
        previousPoint = self.point1coord
        point = self.point2coord
        self.point1coord = point

        # Left click
        if e.button() == 1:
            if previousPoint != self.point2coord:
                if self.edit is False:
                    # First point on line
                    pt = QgsPoint(point)
                    pLine = [pt]
                    ft = QgsFeature()
                    polyline = QgsGeometry.fromPolyline(pLine)
                    ft.setGeometry(polyline)

                    pr = self.lines_layer.dataProvider()
                    pr.addFeatures([ft])

                    self.aslope_list.append(0)
                    self.c_left_slope_list.append(0)
                    self.c_right_slope_list.append(0)

                    self.edit = True
                    self.canvas.refresh()

                else:
                    # Add point
                    pt = QgsPoint(point)
                    ids = [i.id() for i in self.lines_layer.getFeatures()]
                    id = ids[-1]
                    iterator = self.lines_layer.getFeatures(
                        QgsFeatureRequest().setFilterFid(id)
                    )
                    ft = next(iterator)
                    geom = ft.geometry().asPolyline()
                    # Add vertices
                    geom.append(pt)
                    self.line_geom = geom
                    self.aslope_list.append(math.fabs(self.a_slope))
                    self.c_left_slope_list.append(math.fabs(self.c_left_slope))
                    self.c_right_slope_list.append(
                        math.fabs(self.c_right_slope))
                    self.callback(
                        self.a_slope, self.c_left_slope, self.c_right_slope,
                        self.length, self.line_geom, self.aslope_list,
                        self.c_left_slope_list, self.c_right_slope_list, True)
                    pr = self.lines_layer.dataProvider()
                    pr.changeGeometryValues(
                        {ft.id(): QgsGeometry.fromPolyline(geom)})
                    self.canvas.refresh()
                    if self.swath_display is True:
                        self.rub_rect_anchor.reset()
                        self.rub_rect_anchor.addGeometry(
                            QgsGeometry.fromPolyline(geom)
                            .buffer(self.swath_distance, 20), None)

            else:
                # Double click
                pr = self.lines_layer.dataProvider()
                ids = [i.id() for i in self.lines_layer.getFeatures()]
                id = ids[-1]
                iterator = self.lines_layer.getFeatures(
                    QgsFeatureRequest().setFilterFid(id))
                ft = next(iterator)
                geom = ft.geometry().asPolyline()
                if self.swath_display is True:
                    self.rub_rect_anchors.addGeometry(
                        QgsGeometry.fromPolyline(geom)
                        .buffer(self.swath_distance, 20), None)
                if pr.fieldNameIndex('id') == -1:
                    pr.addAttributes([QgsField('id', QVariant.Int, "int", 6)])
                    self.lines_layer.updateFields()
                id_max = 0
                for feat in self.lines_layer.getFeatures():
                    id = feat.attribute('id')
                    if isinstance(id, int) is True:
                        id_max = max(id_max, id)
                new_id = int(id_max) + 1
                index = self.lines_layer.fieldNameIndex("id")
                self.lines_layer.changeAttributeValue(ft.id(), index, new_id)
                self.lines_layer.commitChanges()
                self.lines_layer.startEditing()
                if pr.fieldNameIndex('length') == -1:
                    pr.addAttributes(
                        [QgsField('length', QVariant.Double, "double", 6, 1)])
                    self.lines_layer.updateFields()
                expression = QgsExpression("$length")
                index = self.lines_layer.fieldNameIndex("length")
                value = expression.evaluate(ft)
                self.lines_layer.changeAttributeValue(ft.id(), index, value)
                self.lines_layer.changeAttributeValue(ft.id(), index, value)
                self.lines_layer.commitChanges()
                self.lines_layer.startEditing()
                self.reset()
                self.callback(
                    '', '', '', '', self.line_geom, self.aslope_list,
                    self.c_left_slope_list, self.c_right_slope_list, False)
        # Right click
        else:
            if self.edit is True:
                    pt = QgsPoint(point)
                    ids = [i.id() for i in self.lines_layer.getFeatures()]
                    id = ids[-1]
                    iterator = self.lines_layer.getFeatures(
                        QgsFeatureRequest().setFilterFid(id))
                    ft = next(iterator)
                    geom = ft.geometry().asPolyline()
                    # Add vertices
                    geom.append(pt)
                    self.line_geom = geom
                    self.aslope_list.append(math.fabs(self.a_slope))
                    self.c_left_slope_list.append(math.fabs(self.c_left_slope))
                    self.c_right_slope_list.append(
                        math.fabs(self.c_right_slope))
                    self.callback(
                        self.a_slope, self.c_left_slope, self.c_right_slope,
                        self.length, self.line_geom, self.aslope_list,
                        self.c_left_slope_list, self.c_right_slope_list, True)
                    pr = self.lines_layer.dataProvider()
                    pr.changeGeometryValues(
                        {ft.id(): QgsGeometry.fromPolyline(geom)})
                    self.canvas.refresh()
                    if self.swath_display is True:
                        self.rub_rect_anchors.addGeometry(
                            QgsGeometry.fromPolyline(geom)
                            .buffer(self.swath_distance, 20), None)
                    if pr.fieldNameIndex('id') == -1:
                        pr.addAttributes(
                            [QgsField('id', QVariant.Int, "int", 6)])
                        self.lines_layer.updateFields()
                    id_max = 0
                    for feat in self.lines_layer.getFeatures():
                        id = feat.attribute('id')
                        if isinstance(id, int) is True:
                            id_max = max(id_max, id)
                    new_id = int(id_max) + 1
                    index = self.lines_layer.fieldNameIndex("id")
                    self.lines_layer.changeAttributeValue(
                        ft.id(), index, new_id)
                    self.lines_layer.commitChanges()
                    self.lines_layer.startEditing()
                    if pr.fieldNameIndex('length') == -1:
                        pr.addAttributes(
                            [QgsField(
                                'length', QVariant.Double, "double", 6, 1)])
                        self.lines_layer.updateFields()
                    expression = QgsExpression("$length")
                    index = self.lines_layer.fieldNameIndex("length")
                    value = expression.evaluate(ft)
                    self.lines_layer.changeAttributeValue(
                        ft.id(), index, value)
                    self.lines_layer.commitChanges()
                    self.lines_layer.startEditing()
            self.reset()
            self.callback(
                '', '', '', '', self.line_geom, self.aslope_list,
                self.c_left_slope_list, self.c_right_slope_list, False)

        return None

    # Event when user closes the plugin
    def deactivate(self):
        """Clean variable and buffer when user changes the Maptool"""
        if self.edit is True:
            pr = self.lines_layer.dataProvider()
            ids = [i.id() for i in self.lines_layer.getFeatures()]
            id = ids[-1]
            iterator = self.lines_layer.getFeatures(
                QgsFeatureRequest().setFilterFid(id))
            ft = next(iterator)
            geom = ft.geometry().asPolyline()
            if self.swath_display is True:
                self.rub_rect_anchors.addGeometry(
                    QgsGeometry.fromPolyline(geom)
                    .buffer(self.swath_distance, 20), None)
            if pr.fieldNameIndex('id') == -1:
                pr.addAttributes([QgsField('id', QVariant.Int, "int", 6)])
                self.lines_layer.updateFields()
            id_max = 0
            for feat in self.lines_layer.getFeatures():
                id = feat.attribute('id')
                if id is not None:
                    id_max = max(id_max, id)
            new_id = int(id_max) + 1
            index = self.lines_layer.fieldNameIndex("id")
            self.lines_layer.changeAttributeValue(ft.id(), index, new_id)
            self.lines_layer.commitChanges()
            self.lines_layer.startEditing()
            if pr.fieldNameIndex('length') == -1:
                pr.addAttributes(
                    [QgsField('length', QVariant.Double, "double", 6, 1)])
                self.lines_layer.updateFields()
            expression = QgsExpression("$length")
            index = self.lines_layer.fieldNameIndex("length")
            value = expression.evaluate(ft)
            self.lines_layer.changeAttributeValue(ft.id(), index, value)
            self.lines_layer.changeAttributeValue(ft.id(), index, value)
            self.lines_layer.commitChanges()
            self.lines_layer.startEditing()

        if self.swath_display is True:
            self.rub_rect.reset()
            self.rub_rect_anchor.reset()
            self.rub_rect_anchors.reset()
            self.rub_buff_cursor.reset()
        self.rub_polyline.reset()
        self.rub_cursor.reset()
        self.lines_layer.updateFields()
        self.lines_layer.commitChanges()
        self.callback(None, None, None, None, None, None, None, None, False)

    # Event when user uses 'backspace'
    def keyPressEvent(self, e):
        """Key event :
            - backspace : erase the last point created
            - escape : erase the current track"""
        back_value = u'\x08'
        escape = u'\x1B'
        if e.text() == back_value:
            if self.edit is True:
                # Delete last point
                ids = [i.id() for i in self.lines_layer.getFeatures()]
                id = ids[-1]
                iterator = self.lines_layer.getFeatures(
                    QgsFeatureRequest().setFilterFid(id))
                ft = next(iterator)
                geom = ft.geometry().asPolyline()
                if len(geom) > 1:
                    del geom[-1]
                    self.line_geom = geom
                    del self.aslope_list[-1]
                    del self.c_left_slope_list[-1]
                    del self.c_right_slope_list[-1]
                    self.point1coord = geom[-1]
                    self.callback(
                        '', '', '', '', self.line_geom, self.aslope_list,
                        self.c_left_slope_list, self.c_right_slope_list, True)
                    pr = self.lines_layer.dataProvider()
                    pr.changeGeometryValues(
                        {ft.id(): QgsGeometry.fromPolyline(geom)})
                    self.canvas.refresh()

                    self.rubDisplayUp()
                    if self.swath_display is True:
                        # Actualize rub_rect_anchor
                        self.rub_rect_anchor.reset()
                        self.rub_rect_anchor.addGeometry(
                            QgsGeometry.fromPolyline(geom)
                            .buffer(self.swath_distance, 20), None)
                else:
                    self.lines_layer.commitChanges()
                    self.lines_layer.startEditing()
                    self.lines_layer.deleteFeature(id)
                    self.lines_layer.commitChanges()
                    self.lines_layer.startEditing()
                    self.reset()
                    self.canvas.refresh()
        elif e.text() == escape:
            if self.edit is True:
                self.lines_layer.commitChanges()
                self.lines_layer.startEditing()
                ids = [i.id() for i in self.lines_layer.getFeatures()]
                id = ids[-1]
                iterator = self.lines_layer.getFeatures(
                    QgsFeatureRequest().setFilterFid(id))
                ft = next(iterator)
                geom = ft.geometry().asPolyline()
                i = len(geom)
                for i in range(0, i):
                    del geom[-1]
                    del self.aslope_list[-1]
                    del self.c_left_slope_list[-1]
                    del self.c_right_slope_list[-1]
                self.callback(
                    '', '', '', '', geom, self.aslope_list,
                    self.c_left_slope_list, self.c_right_slope_list, True)
                self.lines_layer.deleteFeature(id)
                self.lines_layer.commitChanges()
                self.lines_layer.startEditing()
                self.reset()
                self.canvas.refresh()

    # When user ends a track
    def reset(self):
        """Reset every variable from the edition, ready to start a new track"""
        self.edit = False
        self.line_geom = None
        self.point1coord = None
        self.point2coord = None
        self.a_slope = None
        self.c_left_slope = None
        self.c_right_slope = None
        self.length = None
        self.aslope_list = []
        self.c_left_slope_list = []
        self.c_right_slope_list = []
        self.rub_polyline.reset()
        if self.swath_display is True:
            self.rub_rect.reset()
            self.rub_rect_anchor.reset()

    # RUBBERBANDS FUNCTIONS
    def rubAnchorsInit(self):
        """Load buffer rubberband from line during maptool activation"""
        rubber = QgsRubberBand(self.canvas, True)

        tracks_layer = self.lines_layer
        for track in tracks_layer.getFeatures():
            geom = track.geometry().asPolyline()
            if geom != 0:
                rubber.addGeometry(
                    QgsGeometry.fromPolyline(geom)
                    .buffer(self.swath_distance, 20), None)
        rubber.setColor(QColor(0, 255, 0, 255))
        rubber.setWidth(2)
        return rubber

    def rubAnchorInit(self):
        """Parameter for the buffer rubberband (after segment construction)"""
        rubber = QgsRubberBand(self.canvas, True)
        rubber.setColor(QColor(0, 255, 0, 255))
        rubber.setWidth(3)
        return rubber

    def rubBuffCursorInit(self):
        """Parameter for the buffer rubberband around the cursor"""
        rubber = QgsRubberBand(self.canvas, True)
        rubber.setColor(QColor(0, 255, 0, 255))
        rubber.setWidth(2)
        return rubber

    def rubCursorInit(self):
        """Parameter for the cursor rubberband"""
        rubber = QgsRubberBand(self.canvas, geometryType=0)
        rubber.setIcon(1)
        rubber.setIconSize(12)
        rubber.setWidth(2)
        rubber.setColor(QColor(235, 10, 190, 255))
        return rubber

    def rubDisplayUp(self):
        """Determine the segment visualisation, depend on the tolerated slopes :
            - red if the user oversteps thresholds
            - green if it's good
            The color is also darker if the segment is too long"""
        self.rub_polyline.reset()

        x1, y1 = self.point1coord
        x2, y2 = self.point2coord
        points = [QgsPoint(x1, y1), QgsPoint(x2, y2)]
        self.rub_polyline.addGeometry(QgsGeometry.fromPolyline(points), None)
        if self.length < self.max_length:
            if self.a_slope < self.tolerated_a_slope \
                and self.a_slope > -(self.tolerated_a_slope) \
                    and self.c_left_slope < self.tolerated_c_slope \
                    and self.c_left_slope > -(self.tolerated_c_slope) \
                    and self.c_right_slope < self.tolerated_c_slope \
                    and self.c_right_slope > -(self.tolerated_c_slope):
                self.rub_polyline.setColor(QColor(0, 255, 0))
            else:
                self.rub_polyline.setColor(QColor(255, 0, 0))
        else:
            if self.a_slope < self.tolerated_a_slope \
                and self.a_slope > -(self.tolerated_a_slope) \
                    and self.c_left_slope < self.tolerated_c_slope \
                    and self.c_left_slope > -(self.tolerated_c_slope) \
                    and self.c_right_slope < self.tolerated_c_slope \
                    and self.c_right_slope > -(self.tolerated_c_slope):
                self.rub_polyline.setColor(QColor(101, 166, 101))
            else:
                self.rub_polyline.setColor(QColor(130, 54, 54))

        if self.swath_display is True:
            self.rubDisplayUpRect(points)

        return None

    def rubDisplayUpRect(self, points):
        self.rub_rect.reset()
        self.rub_rect.addGeometry(
            QgsGeometry.fromPolyline(points)
            .buffer(self.swath_distance, 20), None)

    def rubPolylineInit(self):
        """Parameter for the segment rubberband during segment construction"""
        rubber = QgsRubberBand(self.canvas, False)
        rubber.setWidth(2)
        return rubber

    def rubRectInit(self):
        """Parameter for the buffer rubberband during segment construction"""
        rubber = QgsRubberBand(self.canvas, True)
        rubber.setColor(QColor(0, 255, 0, 255))
        rubber.setWidth(2)
        return rubber

    # Do the slope calc
    def slopeCalc(self, sP, eP):
        """Function to process the slopes, with DEM interpolation"""
        # Retrieve coord
        x1, y1 = sP
        x2, y2 = eP

        # Along slope calculation
        z_start_value = self.zInterpolate(sP)
        z_end_value = self.zInterpolate(eP)

        dist_seg = round(math.sqrt(sP.sqrDist(eP)), 2)

        if z_start_value is not None \
            and z_end_value is not None \
                and dist_seg != 0:
            # a_slope=math.fabs(z_start_value-z_end_value)/dist_seg*100
            a_slope = round((z_end_value - z_start_value) / dist_seg * 100, 2)
        else:
            a_slope = ''

        # Cross slope calculation
        # coord vector
        xv = (x2-x1)
        yv = (y2-y1)
        # centre segment
        xc = (x2-x1)/2+x1
        yc = (y2-y1)/2+y1
        # azimuth
        azimuth = sP.azimuth(eP)
        angle = azimuth - 180

        dist = self.side_distance
        # vecteur directeur buff
        Xv = dist * math.cos(math.radians(angle))
        Yv = dist * math.sin(math.radians(angle))

        # Center value
        center_point = QgsPoint(xc, yc)
        z_center_point_value = self.zInterpolate(center_point)

        # Left side
        x_pointleft_beg = x1 + Xv
        y_pointleft_beg = y1 - Yv
        x_pointleft_cen = xc + Xv
        y_pointleft_cen = yc - Yv
        x_pointleft_end = x2 + Xv
        y_pointleft_end = y2 - Yv

        pointleft_beg = QgsPoint(x_pointleft_beg, y_pointleft_beg)
        z_left_beg_value = self.zInterpolate(pointleft_beg)

        pointleft_cen = QgsPoint(x_pointleft_cen, y_pointleft_cen)
        z_left_cen_value = self.zInterpolate(pointleft_cen)

        pointleft_end = QgsPoint(x_pointleft_end, y_pointleft_end)
        z_left_end_value = self.zInterpolate(pointleft_end)

        if z_left_beg_value is not None and z_start_value is not None \
            and z_left_cen_value is not None \
                and z_center_point_value is not None \
                and z_left_end_value is not None \
                and z_end_value is not None and dist != 0:
            c_left_slope = round(
                (((z_left_beg_value - z_start_value)
                    + (z_left_cen_value - z_center_point_value)
                    + (z_left_end_value - z_end_value)) / 3)/dist * 100, 2)
        else:
            c_left_slope = ''

        # Right side
        x_pointright_beg = x1 - Xv
        y_pointright_beg = y1 + Yv
        x_pointright_cen = xc - Xv
        y_pointright_cen = yc + Yv
        x_pointright_end = x2 - Xv
        y_pointright_end = y2 + Yv

        pointright_beg = QgsPoint(x_pointright_beg, y_pointright_beg)
        z_right_beg_value = self.zInterpolate(pointright_beg)

        pointright_cen = QgsPoint(x_pointright_cen, y_pointright_cen)
        z_right_cen_value = self.zInterpolate(pointright_cen)

        pointright_end = QgsPoint(x_pointright_end, y_pointright_end)
        z_right_end_value = self.zInterpolate(pointright_end)

        if z_right_beg_value is not None and z_start_value is not None \
            and z_right_cen_value is not None \
                and z_center_point_value is not None \
                and z_right_end_value is not None \
                and z_end_value is not None and dist != 0:
            c_right_slope = round(
                (((z_right_beg_value-z_start_value)
                    + (z_right_cen_value-z_center_point_value)
                    + (z_right_end_value-z_end_value))/3)/dist*100, 2)
        else:
            c_right_slope = ''

        return a_slope, c_left_slope, c_right_slope, dist_seg

    def slopeCalcWithoutInterpolate(self, sP, eP):
        """Function to process the slopes, with DEM interpolation"""
        # Retrieve coord
        x1, y1 = sP
        x2, y2 = eP

        # Along slope calculation
        z_start_ident = self.dem.dataProvider().identify(
            sP, QgsRaster.IdentifyFormatValue)
        z_start_value = z_start_ident.results()[1]
        z_end_ident = self.dem.dataProvider().identify(
            eP, QgsRaster.IdentifyFormatValue)
        z_end_value = z_end_ident.results()[1]
        dist_seg = round(math.sqrt(sP.sqrDist(eP)), 2)

        if z_start_value is not None \
            and z_end_value is not None \
                and dist_seg != 0:
            # a_slope=math.fabs(z_start_value-z_end_value)/dist_seg*100
            a_slope = round((z_end_value - z_start_value) / dist_seg * 100, 2)
        else:
            a_slope = ''

        # Cross slope calculation
        # coord vector
        xv = (x2 - x1)
        yv = (y2 - y1)
        # centre segment
        xc = (x2 - x1) / 2 + x1
        yc = (y2 - y1) / 2 + y1
        # azimuth
        azimuth = sP.azimuth(eP)
        angle = azimuth - 180

        dist = self.side_distance
        # vecteur directeur buff
        Xv = dist * math.cos(math.radians(angle))
        Yv = dist * math.sin(math.radians(angle))

        # Center value
        center_point = QgsPoint(xc, yc)
        z_center_point_ident = self.dem.dataProvider().identify(
            center_point, QgsRaster.IdentifyFormatValue)
        z_center_point_value = z_center_point_ident.results()[1]

        # Left side
        x_pointleft_beg = x1 + Xv
        y_pointleft_beg = y1 - Yv
        x_pointleft_cen = xc + Xv
        y_pointleft_cen = yc - Yv
        x_pointleft_end = x2 + Xv
        y_pointleft_end = y2 - Yv

        pointleft_beg = QgsPoint(x_pointleft_beg, y_pointleft_beg)
        z_left_beg_ident = self.dem.dataProvider().identify(
            pointleft_beg, QgsRaster.IdentifyFormatValue)
        z_left_beg_value = z_left_beg_ident.results()[1]

        pointleft_cen = QgsPoint(x_pointleft_cen, y_pointleft_cen)
        z_left_cen_ident = self.dem.dataProvider().identify(
            pointleft_cen, QgsRaster.IdentifyFormatValue)
        z_left_cen_value = z_left_cen_ident.results()[1]

        pointleft_end = QgsPoint(x_pointleft_end, y_pointleft_end)
        z_left_end_ident = self.dem.dataProvider().identify(
            pointleft_end, QgsRaster.IdentifyFormatValue)
        z_left_end_value = z_left_end_ident.results()[1]

        if z_left_beg_value is not None and z_start_value is not None \
            and z_left_cen_value is not None \
                and z_center_point_value is not None \
                and z_left_end_value is not None and z_end_value is not None \
                and dist != 0:
            c_left_slope = round(
                (((z_left_beg_value - z_start_value)
                    + (z_left_cen_value - z_center_point_value)
                    + (z_left_end_value - z_end_value)) / 3)/dist * 100, 2)
        else:
            c_left_slope = ''

        # Right side
        x_pointright_beg = x1 - Xv
        y_pointright_beg = y1 + Yv
        x_pointright_cen = xc - Xv
        y_pointright_cen = yc + Yv
        x_pointright_end = x2 - Xv
        y_pointright_end = y2 + Yv

        pointright_beg = QgsPoint(x_pointright_beg, y_pointright_beg)
        z_right_beg_ident = self.dem.dataProvider().identify(
            pointright_beg, QgsRaster.IdentifyFormatValue)
        z_right_beg_value = z_right_beg_ident.results()[1]

        pointright_cen = QgsPoint(x_pointright_cen, y_pointright_cen)
        z_right_cen_ident = self.dem.dataProvider().identify(
            pointright_cen, QgsRaster.IdentifyFormatValue)
        z_right_cen_value = z_right_cen_ident.results()[1]

        pointright_end = QgsPoint(x_pointright_end, y_pointright_end)
        z_right_end_ident = self.dem.dataProvider().identify(
            pointright_end, QgsRaster.IdentifyFormatValue)
        z_right_end_value = z_right_end_ident.results()[1]

        if z_right_beg_value is not None and z_start_value is not None \
            and z_right_cen_value is not None \
                and z_center_point_value is not None \
                and z_right_end_value is not None \
                and z_end_value is not None and dist != 0:
            c_right_slope = round(
                (((z_right_beg_value-z_start_value)
                    + (z_right_cen_value-z_center_point_value)
                    + (z_right_end_value-z_end_value))/3)/dist*100, 2)
        else:
            c_right_slope = ''

        return a_slope, c_left_slope, c_right_slope, dist_seg

    # SNAP INIT FUNCTION
    def snapperDef(self):
        """Perform snap during edition"""
        snapper = QgsSnappingUtils()
        snapper.readConfigFromProject()
        snapper.setMapSettings(self.canvas.mapSettings())
        return snapper

    def zInterpolate(self, point):
        """Interpolate function (bilinear)"""
        pt1_ident = self.dem.dataProvider().identify(
            point, QgsRaster.IdentifyFormatValue)
        pt1_value = pt1_ident.results()[1]

        x, y = point
        base_x = x % self.x_res
        base_y = y % self.y_res

        if base_x == 0 and base_y == 0:
            pt1 = QgsPoint((x - self.x_res / 2), (y - self.y_res / 2))
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = pt1_ident.results()[1]
            pt2 = QgsPoint((x + self.x_res / 2), (y - self.y_res / 2))
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = (pt1_value + pt2_value + pt3_value + pt4_value) / 4
        elif base_x == 0 and base_y <= (self.y_res / 2):
            pt1 = QgsPoint((x + self.x_res / 2), y)
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x - self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint((x + self / x_res / 2), (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value
                    * math.fabs(self.y_res / 2 - base_y)) / self.y_res)) / 2
        elif base_x == 0 and base_y > (self.y_res / 2):
            pt1 = QgsPoint((x + self / x_res / 2), y)
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x - self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint((x + self / x_res / 2), (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value
                    * math.fabs(self.y_res / 2 - base_y)) / self.y_res)) / 2
        elif base_x <= (self.x_res / 2) and base_y == 0:
            pt1 = QgsPoint(x, (y + self.y_res / 2))
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value + pt3_value) / 2)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value + pt4_value) / 2)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x > (self.x_res / 2) and base_y == 0:
            pt1 = QgsPoint(x, (y + self.y_res / 2))
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x + self.x_res / 2), (y + self.y_res / 2))
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value + pt3_value) / 2)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value + pt4_value) / 2)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x <= (self.x_res / 2) and base_y <= (self.y_res / 2):
            pt2 = QgsPoint((x - self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = (((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value
                    * math.fabs(self.y_res/2 - base_y)) / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res)
        elif base_x <= (self.x_res / 2) and base_y > (self.y_res / 2):
            pt2 = QgsPoint((x - self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value
                    * math.fabs(self.y_res/2 - base_y))
                / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x > (self.x_res / 2) and base_y <= (self.y_res / 2):
            pt2 = QgsPoint((x + self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = (((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value *
                    (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res)
        elif base_x > (self.x_res / 2) and base_y > (self.y_res / 2):
            pt2 = QgsPoint((x + self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value *
                    (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        else:
            z_value = pt1_value
        return z_value


class SelectMapTool(QgsMapTool):
    def __init__(
        self, iface, callback, lines_layer, dem, side_distance, interpolate_act
    ):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.callback = callback
        self.canvas = iface.mapCanvas()
        self.map_tool_name = 'SelectMapTool'

        # Config variables
        self.dem = dem
        self.x_res = self.dem.rasterUnitsPerPixelX()
        self.y_res = self.dem.rasterUnitsPerPixelY()
        self.lines_layer = lines_layer
        self.side_distance = side_distance
        self.interpolate_act = interpolate_act

        # Chart variables
        self.line_geom = None
        self.aslope_list = [0]
        self.c_left_slope_list = [0]
        self.c_right_slope_list = [0]

        # Geometric variables
        self.a_slope = None
        self.c_left_slope = None
        self.c_right_slope = None
        self.length = None

        # Rubberband init
        self.rub_polyline = self.rubPolylineInit()
        self.reset()
        return None

    def canvasReleaseEvent(self, e):
        """Click event"""
        result = self.identify(e)

    def deactivate(self):
        """Clean variable and buffer when user changes the Maptool"""
        self.reset()

    def identify(self, e):
        """Select the track entity and display its graph"""
        self.reset()
        pt = self.canvas.getCoordinateTransform().toMapPoint(
            e.pos().x(), e.pos().y())
        scale = self.canvas.mapUnitsPerPixel()
        pix_tol = 10
        pt_geom = QgsGeometry().fromPoint(pt)
        pt_geom = pt_geom.buffer(scale*pix_tol, 20)
        catch = False
        result = None
        geom = None
        for ft in self.lines_layer.getFeatures():
            if pt_geom.intersects(ft.geometry()):
                result = ft
                break
        if result:
            geom = result.geometry().asPolyline()
            self.rub_polyline.addGeometry(result.geometry(), self.lines_layer)
            ln = len(geom)
            print ln
            id_error_list = []
            for i in range(0, ln-1):
                if self.interpolate_act is True:
                    self.a_slope, self.c_left_slope, \
                        self.c_right_slope, self.length = (
                            self.slopeCalc(geom[i], geom[i+1]))
                    if self.length != 0:
                        self.aslope_list.append(math.fabs(self.a_slope))
                        self.c_left_slope_list.append(
                            math.fabs(self.c_left_slope))
                        self.c_right_slope_list.append(
                            math.fabs(self.c_right_slope))
                    else:
                        id_error_list.append(i+1)

                else:
                    self.a_slope, self.c_left_slope, \
                        self.c_right_slope, self.length = (
                            self.slopeCalcWithoutInterpolate(
                                geom[i], geom[i+1]))
                    if self.length != 0:
                        self.aslope_list.append(math.fabs(self.a_slope))
                        self.c_left_slope_list.append(
                            math.fabs(self.c_left_slope))
                        self.c_right_slope_list.append(
                            math.fabs(self.c_right_slope))
                    else:
                        id_error_list.append(i+1)

                if len(id_error_list) != 0:
                    for id in id_error_list:
                        del geom[id]
        if geom:
            self.callback(
                geom, self.aslope_list, self.c_left_slope_list,
                self.c_right_slope_list)

    def reset(self):
        """Reset attributes"""
        self.line_geom = None
        self.aslope_list = [0]
        self.c_left_slope_list = [0]
        self.c_right_slope_list = [0]
        self.rub_polyline.reset()

    def rubPolylineInit(self):
        """Parameter for the segment rubberband (during segment selection)"""
        rubber = QgsRubberBand(self.canvas, False)
        rubber.setWidth(4)
        rubber.setColor(QColor(255, 255, 0, 255))
        return rubber

    # Do the slope calc
    def slopeCalc(self, sP, eP):
        """Function to process the slopes, with DEM interpolation"""
        # Retrieve coord
        x1, y1 = sP
        x2, y2 = eP

        # Along slope calculation
        z_start_value = self.zInterpolate(sP)
        z_end_value = self.zInterpolate(eP)

        dist_seg = math.sqrt(sP.sqrDist(eP))

        if (
            z_start_value is not None
            and z_end_value is not None and dist_seg != 0
        ):
            a_slope = round((z_end_value - z_start_value) / dist_seg * 100, 2)
        else:
            a_slope = ''

        # Cross slope calculation
        # coord vector
        xv = (x2-x1)
        yv = (y2-y1)
        # centre segment
        xc = (x2-x1)/2+x1
        yc = (y2-y1)/2+y1
        # azimuth
        azimuth = sP.azimuth(eP)
        angle = azimuth - 180

        dist = self.side_distance
        # vecteur directeur buff
        Xv = dist * math.cos(math.radians(angle))
        Yv = dist * math.sin(math.radians(angle))

        # Center value
        center_point = QgsPoint(xc, yc)
        z_center_point_value = self.zInterpolate(center_point)

        # Left side
        x_pointleft_beg = x1 + Xv
        y_pointleft_beg = y1 - Yv
        x_pointleft_cen = xc + Xv
        y_pointleft_cen = yc - Yv
        x_pointleft_end = x2 + Xv
        y_pointleft_end = y2 - Yv

        pointleft_beg = QgsPoint(x_pointleft_beg, y_pointleft_beg)
        z_left_beg_value = self.zInterpolate(pointleft_beg)

        pointleft_cen = QgsPoint(x_pointleft_cen, y_pointleft_cen)
        z_left_cen_value = self.zInterpolate(pointleft_cen)

        pointleft_end = QgsPoint(x_pointleft_end, y_pointleft_end)
        z_left_end_value = self.zInterpolate(pointleft_end)

        if (
            z_left_beg_value is not None and z_start_value is not None
            and z_left_cen_value is not None
            and z_center_point_value is not None
            and z_left_end_value is not None
            and z_end_value is not None and dist != 0
        ):
            c_left_slope = round(
                (((z_left_beg_value - z_start_value)
                    + (z_left_cen_value - z_center_point_value)
                    + (z_left_end_value - z_end_value)) / 3)/dist * 100, 2)
        else:
            c_left_slope = ''

        # Right side
        x_pointright_beg = x1 - Xv
        y_pointright_beg = y1 + Yv
        x_pointright_cen = xc - Xv
        y_pointright_cen = yc + Yv
        x_pointright_end = x2 - Xv
        y_pointright_end = y2 + Yv

        pointright_beg = QgsPoint(x_pointright_beg, y_pointright_beg)
        z_right_beg_value = self.zInterpolate(pointright_beg)

        pointright_cen = QgsPoint(x_pointright_cen, y_pointright_cen)
        z_right_cen_value = self.zInterpolate(pointright_cen)

        pointright_end = QgsPoint(x_pointright_end, y_pointright_end)
        z_right_end_value = self.zInterpolate(pointright_end)

        if (
            z_right_beg_value is not None and z_start_value is not None
            and z_right_cen_value is not None
            and z_center_point_value is not None
            and z_right_end_value is not None
            and z_end_value is not None and dist != 0
        ):
            c_right_slope = round(
                (((z_right_beg_value - z_start_value)
                    + (z_right_cen_value - z_center_point_value)
                    + (z_right_end_value - z_end_value)) / 3) / dist * 100, 2)
        else:
            c_right_slope = ''

        return a_slope, c_left_slope, c_right_slope, dist_seg

    def slopeCalcWithoutInterpolate(self, sP, eP):
        """Function to process the slopes, with DEM interpolation"""
        # Retrieve coord
        x1, y1 = sP
        x2, y2 = eP

        # Along slope calculation
        z_start_ident = self.dem.dataProvider().identify(
            sP, QgsRaster.IdentifyFormatValue)
        z_start_value = z_start_ident.results()[1]
        z_end_ident = self.dem.dataProvider().identify(
            eP, QgsRaster.IdentifyFormatValue)
        z_end_value = z_end_ident.results()[1]
        dist_seg = math.sqrt(sP.sqrDist(eP))

        if (
            z_start_value is not None and z_end_value is not None
            and dist_seg != 0
        ):
            a_slope = round((z_end_value - z_start_value) / dist_seg * 100, 2)
        else:
            a_slope = ''

        # Cross slope calculation
        # coord vector
        xv = (x2 - x1)
        yv = (y2 - y1)
        # centre segment
        xc = (x2 - x1) / 2 + x1
        yc = (y2 - y1)/2 + y1
        # azimuth
        azimuth = sP.azimuth(eP)
        angle = azimuth-180

        dist = self.side_distance
        # vecteur directeur buff
        Xv = dist * math.cos(math.radians(angle))
        Yv = dist * math.sin(math.radians(angle))

        # Center value
        center_point = QgsPoint(xc, yc)
        z_center_point_ident = self.dem.dataProvider().identify(
            center_point, QgsRaster.IdentifyFormatValue)
        z_center_point_value = z_center_point_ident.results()[1]

        # Left side
        x_pointleft_beg = x1 + Xv
        y_pointleft_beg = y1 - Yv
        x_pointleft_cen = xc + Xv
        y_pointleft_cen = yc - Yv
        x_pointleft_end = x2 + Xv
        y_pointleft_end = y2 - Yv

        pointleft_beg = QgsPoint(x_pointleft_beg, y_pointleft_beg)
        z_left_beg_ident = self.dem.dataProvider().identify(
            pointleft_beg, QgsRaster.IdentifyFormatValue)
        z_left_beg_value = z_left_beg_ident.results()[1]

        pointleft_cen = QgsPoint(x_pointleft_cen, y_pointleft_cen)
        z_left_cen_ident = self.dem.dataProvider().identify(
            pointleft_cen, QgsRaster.IdentifyFormatValue)
        z_left_cen_value = z_left_cen_ident.results()[1]

        pointleft_end = QgsPoint(x_pointleft_end, y_pointleft_end)
        z_left_end_ident = self.dem.dataProvider().identify(
            pointleft_end, QgsRaster.IdentifyFormatValue)
        z_left_end_value = z_left_end_ident.results()[1]

        if (
            z_left_beg_value is not None
            and z_start_value is not None
            and z_left_cen_value is not None
            and z_center_point_value is not None
            and z_left_end_value is not None
            and z_end_value is not None and dist != 0
        ):
            c_left_slope = round(
                (((z_left_beg_value - z_start_value)
                    + (z_left_cen_value - z_center_point_value)
                    + (z_left_end_value - z_end_value)) / 3)/dist * 100, 2)
        else:
            c_left_slope = ''

        # Right side
        x_pointright_beg = x1 - Xv
        y_pointright_beg = y1 + Yv
        x_pointright_cen = xc - Xv
        y_pointright_cen = yc + Yv
        x_pointright_end = x2 - Xv
        y_pointright_end = y2 + Yv

        pointright_beg = QgsPoint(x_pointright_beg, y_pointright_beg)
        z_right_beg_ident = self.dem.dataProvider().identify(
            pointright_beg, QgsRaster.IdentifyFormatValue)
        z_right_beg_value = z_right_beg_ident.results()[1]

        pointright_cen = QgsPoint(x_pointright_cen, y_pointright_cen)
        z_right_cen_ident = self.dem.dataProvider().identify(
            pointright_cen, QgsRaster.IdentifyFormatValue)
        z_right_cen_value = z_right_cen_ident.results()[1]

        pointright_end = QgsPoint(x_pointright_end, y_pointright_end)
        z_right_end_ident = self.dem.dataProvider().identify(
            pointright_end, QgsRaster.IdentifyFormatValue)
        z_right_end_value = z_right_end_ident.results()[1]

        if (
            z_right_beg_value is not None and z_start_value is not None
            and z_right_cen_value is not None
            and z_center_point_value is not None
            and z_right_end_value is not None
            and z_end_value is not None and dist != 0
        ):
            c_right_slope = round(
                (((z_right_beg_value - z_start_value)
                    + (z_right_cen_value - z_center_point_value)
                    + (z_right_end_value - z_end_value)) / 3) / dist * 100, 2)
        else:
            c_right_slope = ''

        return a_slope, c_left_slope, c_right_slope, dist_seg

    def zInterpolate(self, point):
        """Interpolate function (bilinear)"""
        pt1_ident = self.dem.dataProvider().identify(
            point, QgsRaster.IdentifyFormatValue)
        pt1_value = pt1_ident.results()[1]

        x, y = point
        base_x = x % self.x_res
        base_y = y % self.y_res

        if base_x == 0 and base_y == 0:
            pt1 = QgsPoint((x - self.x_res / 2), (y - self.y_res / 2))
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = pt1_ident.results()[1]
            pt2 = QgsPoint((x + self.x_res / 2), (y - self.y_res / 2))
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = (pt1_value + pt2_value + pt3_value + pt4_value) / 4
        elif base_x == 0 and base_y <= (self.y_res / 2):
            pt1 = QgsPoint((x+self.x_res / 2), y)
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x-self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint((x+self/x_res / 2), (y-self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x-self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = (
                ((pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)) / 2
        elif base_x == 0 and base_y > (self.y_res / 2):
            pt1 = QgsPoint((x + self / x_res / 2), y)
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x - self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint((x + self / x_res / 2), (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res/2 - base_y))
                / self.y_res)
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value
                    * math.fabs(self.y_res / 2 - base_y)) / self.y_res)) / 2
        elif base_x <= (self.x_res / 2) and base_y == 0:
            pt1 = QgsPoint(x, (y+self.y_res/2))
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value + pt3_value) / 2)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value + pt4_value) / 2)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x > (self.x_res / 2) and base_y == 0:
            pt1 = QgsPoint(x, (y + self.y_res / 2))
            pt1_ident = self.dem.dataProvider().identify(
                pt1, QgsRaster.IdentifyFormatValue)
            pt1_value = z_pt1_ident.results()[1]
            pt2 = QgsPoint((x + self.x_res / 2), (y + self.y_res / 2))
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value + pt3_value) / 2)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value+pt4_value) / 2)
                * math.fabs(self.x_res/2 - base_x)) / self.x_res
        elif base_x <= (self.x_res/2) and base_y <= (self.y_res/2):
            pt2 = QgsPoint((x-self.x_res/2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y-self.y_res/2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x-self.x_res/2), (y-self.y_res/2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value*(self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x <= (self.x_res / 2) and base_y > (self.y_res / 2):
            pt2 = QgsPoint((x - self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x - self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                 + pt3_value
                 * math.fabs(self.y_res / 2 - base_y)) / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x > (self.x_res / 2) and base_y <= (self.y_res / 2):
            pt2 = QgsPoint((x + self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y - self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y - self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = ((
                (pt1_value * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value * math.fabs(self.y_res / 2 - base_y))
                / self.y_res)
                * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                + ((pt2_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt4_value * math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                * math.fabs(self.x_res / 2 - base_x)) / self.x_res
        elif base_x > (self.x_res / 2) and base_y > (self.y_res / 2):
            pt2 = QgsPoint((x + self.x_res / 2), y)
            pt2_ident = self.dem.dataProvider().identify(
                pt2, QgsRaster.IdentifyFormatValue)
            pt2_value = pt2_ident.results()[1]
            pt3 = QgsPoint(x, (y + self.y_res / 2))
            pt3_ident = self.dem.dataProvider().identify(
                pt3, QgsRaster.IdentifyFormatValue)
            pt3_value = pt3_ident.results()[1]
            pt4 = QgsPoint((x + self.x_res / 2), (y + self.y_res / 2))
            pt4_ident = self.dem.dataProvider().identify(
                pt4, QgsRaster.IdentifyFormatValue)
            pt4_value = pt4_ident.results()[1]
            z_value = (
                (((pt1_value
                    * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                    + pt3_value*math.fabs(self.y_res / 2 - base_y))
                    / self.y_res)
                    * (self.x_res - math.fabs(self.x_res / 2 - base_x))
                    + ((pt2_value
                        * (self.y_res - math.fabs(self.y_res / 2 - base_y))
                        + pt4_value * math.fabs(self.y_res / 2 - base_y))
                        / self.y_res)
                    * math.fabs(self.x_res / 2 - base_x)) / self.x_res
            )
        else:
            z_value = pt1_value
        return z_value
