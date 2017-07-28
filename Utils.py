# -*- coding: utf-8 -*-
"""
***************************************************************************
 Slope_road
								 A QGIS plugin
 Tools to calculate along and cross slope for road
							  -------------------
		begin				 : 2017-03-22
		git sha				 : 2017-06-20:11
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

from qgis.core import *
from qgis.gui import *
from qgis.gui import QgsRubberBand
from PyQt4.QtGui import QColor
from PyQt4.QtCore import QVariant
import math
import time

class SlopeMapTool(QgsMapTool):
    def __init__(self,iface, callback, lines_layer, dem, side_distance, tolerated_slope, max_length, swath_distance):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface              = iface
        self.callback           = callback
        self.canvas             = iface.mapCanvas()
        self.dem                = dem
        self.lines_layer        = lines_layer
        self.line_geom          = None
        self.aslope_list        = []
        self.c_left_slope_list  = []
        self.c_right_slope_list = []
        self.side_distance      = side_distance
        self.max_length         = max_length
        self.tolerated_slope    = tolerated_slope
        self.swath_distance     = swath_distance
        self.edit               = False
        self.point1coord        = None
        self.point2coord        = None
        self.a_slope            = None
        self.c_left_slope       = None
        self.c_right_slope      = None
        # self.cSlope           = None
        self.length             = None
        self.rub_polyline       = QgsRubberBand(self.canvas, False)
        self.rub_rect           = QgsRubberBand(self.canvas, True)
        self.rub_rect_anchor    = QgsRubberBand(self.canvas, True)
        self.rub_rect_anchors   = QgsRubberBand(self.canvas, True)
        self.rub_cursor         = QgsRubberBand(self.canvas, True)
        return None
        
    #Event when user move the mouse : it will define a second point and launch slopeCalc function.
    def canvasMoveEvent(self,e):        
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        self.point2coord = point
        self.rub_cursor.reset()
        self.rub_cursor.addGeometry(QgsGeometry.fromPoint(QgsPoint(self.point2coord[0], self.point2coord[1])).buffer(self.swath_distance,20),None)
        self.rub_cursor.setColor(QColor(0,255,0,50))
        self.rub_cursor.setWidth(2)
        
        if self.point1coord != None and self.point2coord != None and self.point1coord != self.point2coord :
            self.a_slope, self.c_left_slope, self.c_right_slope, self.length = self.slopeCalc(self.point1coord, self.point2coord)
        self.callback(self.a_slope, self.c_left_slope, self.c_right_slope, self.length, self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, False)
        
        if self.point1coord != None and self.point2coord != None and self.point1coord != self.point2coord :
            self.rubDisplayUp()
        return None
    
    def canvasReleaseEvent(self,e):
        previousPoint = self.point1coord
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(),e.pos().y())
        self.point1coord = point
        
        #Left click
        if e.button() == 1 :
            if previousPoint != self.point2coord :
                if self.edit == False :
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
                    
                else :
                    pt = QgsPoint(point)
                    ids = [i.id() for i in self.lines_layer.getFeatures()]
                    id = ids[-1]
                    iterator = self.lines_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
                    ft = next(iterator)
                    geom = ft.geometry().asPolyline()
                    #add vertices
                    geom.append(pt)
                    self.line_geom = geom
                    self.aslope_list.append(math.fabs(self.a_slope))
                    self.c_left_slope_list.append(math.fabs(self.c_left_slope))
                    self.c_right_slope_list.append(math.fabs(self.c_right_slope))
                    self.callback(self.a_slope, self.c_left_slope, self.c_right_slope, self.length, self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, True)
                    pr = self.lines_layer.dataProvider()
                    pr.changeGeometryValues({ft.id():QgsGeometry.fromPolyline(geom)})
                    self.canvas.refresh()
                    self.rub_rect_anchor.reset()
                    self.rub_rect_anchor.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20), None)
                    self.rub_rect_anchor.setColor(QColor(0,255,0,50))
                    self.rub_rect_anchor.setWidth(2)
            else :
                pr = self.lines_layer.dataProvider()
                ids = [i.id() for i in self.lines_layer.getFeatures()]
                id = ids[-1]
                iterator = self.lines_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
                ft = next(iterator)
                geom = ft.geometry().asPolyline()
                self.rub_rect_anchors.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20), None)
                self.rub_rect_anchors.setColor(QColor(0,255,0,50))
                self.rub_rect_anchors.setWidth(2)
                if pr.fieldNameIndex('length') == -1 :
                    pr.addAttributes([QgsField('length', QVariant.Double,"double",6,1)] )
                    self.lines_layer.updateFields()
                expression= QgsExpression("$length")
                index=self.lines_layer.fieldNameIndex("length")
                value = expression.evaluate(ft)
                self.lines_layer.changeAttributeValue(ft.id(),index,value)
                self.lines_layer.commitChanges()
                self.lines_layer.startEditing()
                self.reset()
                self.callback('', '', '', '', self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, False)
        #Right click
        else :
            if self.edit == True :
                    pt = QgsPoint(point)
                    ids = [i.id() for i in self.lines_layer.getFeatures()]
                    id = ids[-1]
                    iterator = self.lines_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
                    ft = next(iterator)
                    geom = ft.geometry().asPolyline()
                    #add vertices
                    geom.append(pt)
                    self.line_geom = geom
                    self.aslope_list.append(math.fabs(self.a_slope))
                    self.c_left_slope_list.append(math.fabs(self.c_left_slope))
                    self.c_right_slope_list.append(math.fabs(self.c_right_slope))
                    self.callback(self.a_slope, self.c_left_slope, self.c_right_slope, self.length, self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, True)
                    pr = self.lines_layer.dataProvider()
                    pr.changeGeometryValues({ft.id():QgsGeometry.fromPolyline(geom)})
                    self.canvas.refresh()
                    self.rub_rect_anchors.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20), None)
                    self.rub_rect_anchors.setColor(QColor(0,255,0,50))
                    self.rub_rect_anchors.setWidth(2)
                    if pr.fieldNameIndex('length') == -1 :
                        pr.addAttributes([QgsField('length', QVariant.Double,"double",6,1)] )
                        self.lines_layer.updateFields()
                    expression= QgsExpression("$length")
                    index=self.lines_layer.fieldNameIndex("length")
                    value = expression.evaluate(ft)
                    self.lines_layer.changeAttributeValue(ft.id(),index,value)
                    self.lines_layer.commitChanges()
                    self.lines_layer.startEditing()
            self.reset()
            self.callback('', '', '', '', self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, False)        
            
        return None
    
    def reset(self) :
        self.edit                   = False
        self.line_geom              = None
        self.point1coord            = None
        self.point2coord            = None
        self.a_slope                = None
        self.c_left_slope           = None
        self.c_right_slope          = None
        self.length                 = None
        self.aslope_list            = []
        self.c_left_slope_list      = []
        self.c_right_slope_list     = []
        self.rub_polyline.reset()
        self.rub_rect.reset()
        self.rub_rect_anchor.reset()
    
    def deactivate(self) :
        self.rub_polyline.reset()
        self.rub_rect.reset()
        self.rub_rect_anchor.reset()
        self.rub_rect_anchors.reset()
        self.rub_cursor.reset()
        self.lines_layer.updateFields()
        self.lines_layer.commitChanges()
    
    def keyPressEvent(self,e):
        back_value = u'\x08'
        if e.text() == back_value :
            if self.edit == True :
                #delete last point
                ids = [i.id() for i in self.lines_layer.getFeatures()]
                id = ids[-1]
                iterator = self.lines_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
                ft = next(iterator)
                geom = ft.geometry().asPolyline()
                del geom[-1]
                self.line_geom = geom
                del self.aslope_list[-1]
                del self.c_left_slope_list[-1]
                del self.c_right_slope_list[-1]
                self.point1coord = geom[-1]
                self.callback('', '', '', '', self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, True)
                pr = self.lines_layer.dataProvider()
                pr.changeGeometryValues({ft.id():QgsGeometry.fromPolyline(geom)})
                self.canvas.refresh()
                self.rubDisplayUp()
                #actualize rub_rect_anchor
                self.rub_rect_anchor.reset()
                self.rub_rect_anchor.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20),None)
    
    #Do the slope calc
    def slopeCalc(self, sP, eP) :
        # #Retrieve coord
        x1, y1 = sP
        x2, y2 = eP
        
        # Along slope calculation
        z_start_ident = self.dem.dataProvider().identify(sP, QgsRaster.IdentifyFormatValue)
        z_start_value = z_start_ident.results()[1]
        z_end_ident = self.dem.dataProvider().identify(eP, QgsRaster.IdentifyFormatValue)
        z_end_value = z_end_ident.results()[1]
        dist_seg = math.sqrt(sP.sqrDist(eP))

        if (z_start_value != None and z_end_value != None and dist_seg != 0) :
            # a_slope=math.fabs(z_start_value-z_end_value)/dist_seg*100
            a_slope = round((z_end_value - z_start_value) / dist_seg * 100, 2)
        else :
            a_slope = ''
        
        # Cross slope calculation
        #coord vector
        xv = (x2-x1)
        yv = (y2-y1)
        #centre segment
        xc = (x2-x1)/2+x1
        yc = (y2-y1)/2+y1
        #azimuth
        azimuth=sP.azimuth(eP)
        angle=azimuth-180
        # TO DO : PUT dist AS USER INPUT
        dist=self.side_distance
        #vecteur directeur buff
        Xv= dist * math.cos(math.radians(angle))
        Yv= dist * math.sin(math.radians(angle))
        
        #Center value
        center_point = QgsPoint(xc, yc)
        z_center_point_ident = self.dem.dataProvider().identify(center_point, QgsRaster.IdentifyFormatValue)
        z_center_point_value = z_center_point_ident.results()[1]
        
        #Left side
        x_pointleft_beg = x1 + Xv
        y_pointleft_beg = y1 - Yv
        x_pointleft_cen = xc + Xv
        y_pointleft_cen = yc - Yv
        x_pointleft_end = x2 + Xv
        y_pointleft_end = y2 - Yv
        
        pointleft_beg = QgsPoint(x_pointleft_beg, y_pointleft_beg)
        z_left_beg_ident = self.dem.dataProvider().identify(pointleft_beg, QgsRaster.IdentifyFormatValue)
        z_left_beg_value = z_left_beg_ident.results()[1]
        pointleft_cen = QgsPoint(x_pointleft_cen, y_pointleft_cen)
        z_left_cen_ident = self.dem.dataProvider().identify(pointleft_cen, QgsRaster.IdentifyFormatValue)
        z_left_cen_value = z_left_cen_ident.results()[1]
        pointleft_end = QgsPoint(x_pointleft_end, y_pointleft_end)
        z_left_end_ident = self.dem.dataProvider().identify(pointleft_end, QgsRaster.IdentifyFormatValue)
        z_left_end_value = z_left_end_ident.results()[1]
        if z_left_beg_value != None and z_start_value != None and z_left_cen_value != None and z_center_point_value != None and z_left_end_value != None and z_end_value != None and dist != 0 :
            c_left_slope = round((((z_left_beg_value - z_start_value) + (z_left_cen_value - z_center_point_value) + (z_left_end_value - z_end_value)) / 3)/dist * 100, 2)
        else :
            c_left_slope = ''
        
        #Right side
        x_pointright_beg = x1 - Xv
        y_pointright_beg = y1 + Yv
        x_pointright_cen = xc - Xv
        y_pointright_cen = yc + Yv
        x_pointright_end = x2 - Xv
        y_pointright_end = y2 + Yv
        
        pointright_beg = QgsPoint(x_pointright_beg,y_pointright_beg)
        z_right_beg_ident = self.dem.dataProvider().identify(pointright_beg,QgsRaster.IdentifyFormatValue)
        z_right_beg_value = z_right_beg_ident.results()[1]
        pointright_cen = QgsPoint(x_pointright_cen,y_pointright_cen)
        z_right_cen_ident = self.dem.dataProvider().identify(pointright_cen,QgsRaster.IdentifyFormatValue)
        z_right_cen_value = z_right_cen_ident.results()[1]
        pointright_end = QgsPoint(x_pointright_end,y_pointright_end)
        z_right_end_ident = self.dem.dataProvider().identify(pointright_end,QgsRaster.IdentifyFormatValue)
        z_right_end_value = z_right_end_ident.results()[1]
        if z_right_beg_value != None and z_start_value != None and z_right_cen_value != None and z_center_point_value != None and z_right_end_value != None and z_end_value != None and dist != 0 :
            c_right_slope = round((((z_right_beg_value-z_start_value)+(z_right_cen_value-z_center_point_value)+(z_right_end_value-z_end_value))/3)/dist*100,2)
        else :
            c_right_slope = ''
        
        #point buff (old method)
        # x_pointleft=xc+Xv
        # y_pointleft=yc-Yv
        # x_pointright=xc-Xv
        # y_pointright=yc+Yv
        # pointleft = QgsPoint(x_pointleft,y_pointleft)
        # zLeftIdent = self.dem.dataProvider().identify(pointleft,QgsRaster.IdentifyFormatValue)
        # zLeftValue = zLeftIdent.results()[1]
        # pointright = QgsPoint(x_pointright,y_pointright)
        # zRightIdent = self.dem.dataProvider().identify(pointright,QgsRaster.IdentifyFormatValue)
        # zRightValue = zRightIdent.results()[1]
        # if (zLeftValue != None and zRightValue != None and dist!=0) :
            # cSlope=round(math.fabs(zLeftValue - zRightValue)/(dist*2)*100,2)
        # else :
            # cSlope=None
        return a_slope, c_left_slope, c_right_slope, dist_seg

    def rubDisplayUp(self) :
        self.rub_polyline.reset()
        self.rub_rect.reset()
        x1, y1 = self.point1coord
        x2, y2 = self.point2coord
        points = [ QgsPoint(x1,y1),QgsPoint(x2,y2)]
        self.rub_polyline.addGeometry(QgsGeometry.fromPolyline(points), None)
        self.rub_polyline.setWidth(2)
        if self.length < self.max_length :
            if self.a_slope < self.tolerated_slope and self.a_slope > -(self.tolerated_slope) :
                self.rub_polyline.setColor(QColor(0, 255, 0))
            else :
                self.rub_polyline.setColor(QColor(255, 0, 0))
        else :
            if self.a_slope < self.tolerated_slope and self.a_slope > -(self.tolerated_slope) :
                self.rub_polyline.setColor(QColor(101, 166, 101))
            else :
                self.rub_polyline.setColor(QColor(130, 54, 54))
        
        self.rub_rect.addGeometry(QgsGeometry.fromPolyline(points).buffer(self.swath_distance,20),None)
        # self.rub_rect.setFillColor(QColor(0,255,0,50))
        self.rub_rect.setColor(QColor(0,255,0,50))
        return None

