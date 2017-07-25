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
import math
import time

class SlopeMapTool(QgsMapTool):
    def __init__(self,iface, callback, lines_layer, dem, side_distance, tolerated_slope, swath_distance):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface           = iface
        self.callback        = callback
        self.canvas          = iface.mapCanvas()
        # self.trackslayer   = trackslayer
        self.dem             = dem
        self.lines_layer     = lines_layer
        self.side_distance   = side_distance
        self.tolerated_slope = tolerated_slope
        self.swath_distance  = swath_distance
        self.edit            = False
        self.point1coord     = None
        self.point2coord     = None
        self.a_slope         = None
        self.c_left_slope    = None
        self.c_right_slope   = None
        # self.cSlope        = None
        self.length          = None
        self.rub_polyline    = QgsRubberBand(self.canvas, False)
        self.rub_rect        = QgsRubberBand(self.canvas, True)
        return None
        
    #Event when user move the mouse : it will define a second point and launch slopeCalc function.
    def canvasMoveEvent(self,e):        
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        self.point2coord = point
        
        if self.point1coord != None and self.point2coord != None and self.point1coord != self.point2coord :
            self.a_slope, self.c_left_slope, self.c_right_slope, self.length = self.slopeCalc(self.point1coord, self.point2coord)
        self.callback(self.a_slope, self.c_left_slope, self.c_right_slope, self.length)
        
        if self.point1coord != None and self.point2coord != None and self.point1coord != self.point2coord :
            self.rub_polyline.reset()
            self.rub_rect.reset()
            x1, y1 = self.point1coord
            x2, y2 = self.point2coord
            points = [ QgsPoint(x1,y1),QgsPoint(x2,y2)]
            self.rub_polyline.addGeometry(QgsGeometry.fromPolyline(points), None)
            self.rub_polyline.setWidth(2)
            if self.a_slope < self.tolerated_slope and self.a_slope > -(self.tolerated_slope) :
                self.rub_polyline.setColor(QColor(0, 255, 0))
            else :
                self.rub_polyline.setColor(QColor(255, 0, 0))
            
            azimuth = self.point1coord.azimuth(self.point2coord)
            angle = azimuth - 180
            # TO DO : PUT dist AS USER INPUT
            dist= self.swath_distance
            #vecteur directeur buff
            Xv = dist * math.cos(math.radians(angle))
            Yv = dist * math.sin(math.radians(angle))
            #point buff
            x1_pointleft = x1 - Xv
            y1_pointleft = y1 + Yv
            x1_pointright = x1 + Xv
            y1_pointright = y1 - Yv
            x2_pointleft = x2 - Xv
            y2_pointleft = y2 + Yv
            x2_pointright = x2 + Xv
            y2_pointright = y2 - Yv
            rect=[[ QgsPoint(x1_pointleft, y1_pointleft), QgsPoint(x2_pointleft, y2_pointleft), QgsPoint(x2_pointright, y2_pointright), QgsPoint(x1_pointright, y1_pointright)]]
            self.rub_rect.addGeometry(QgsGeometry.fromPolygon(rect),None)
            # self.rub_rect.setFillColor(QColor(0,255,0,50))
            self.rub_rect.setColor(QColor(0,255,0,50))
        return None
    
    def canvasReleaseEvent(self,e):
        previousPoint = self.point1coord
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(),e.pos().y())
        self.point1coord = point
        if previousPoint != self.point2coord :
            if self.edit == False :
                pt = QgsPoint(point)
                pLine = [pt]
                ft = QgsFeature()
                polyline = QgsGeometry.fromPolyline(pLine)
                ft.setGeometry(polyline)
                
                pr = self.lines_layer.dataProvider()
                pr.addFeatures([ft])
                
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
                pr = self.lines_layer.dataProvider()
                pr.changeGeometryValues({ft.id():QgsGeometry.fromPolyline(geom)})
                self.canvas.refresh()
        else :
            self.reset()
            self.callback('', '', '', '')
        return None
    
    def canvasDoubleClickEvent(self,e):
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        pt = QgsPoint(point)
        ids = [i.id() for i in self.lines_layer.getFeatures()]
        id = ids[-1]
        iterator = self.lines_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
        ft = next(iterator)
        geom = ft.geometry().asPolyline()
        #add vertices
        geom.append(pt)
        pr = self.lines_layer.dataProvider()
        pr.changeGeometryValues({ft.id():QgsGeometry.fromPolyline(geom)})
        self.canvas.refresh()
        self.edit = False
        return None
    
    def reset(self) :
        self.edit = False
        self.point1coord = None
        self.point2coord = None
        self.a_slope = None
        self.c_left_slope = None
        self.c_right_slope = None
        self.length = None
        self.rub_polyline.reset()
        self.rub_rect.reset()
    
    def desactivate(self) :
        self.rub_polyline.reset()
        self.rub_rect.reset()
    
    
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


