# -*- coding: utf-8 -*-
"""
***************************************************************************
 Slope_road
								 A QGIS plugin
 Tools to calculate along and cross slope for road
							  -------------------
		begin				 : 2017-03-22
		git sha				 : 2017-07-07
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
from qgis.gui import QgsMapToolIdentify
from PyQt4.QtGui import QColor
from PyQt4.QtCore import QVariant
import math
import time

class SlopeMapTool(QgsMapTool):
    def __init__(self,iface, callback, lines_layer, dem, side_distance, tolerated_a_slope, tolerated_c_slope, max_length, swath_distance, max_length_hold, swath_display):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface              = iface
        self.callback           = callback
        self.canvas             = iface.mapCanvas()
        self.map_tool_name      = 'SlopeMapTool'
        
        #Config variables
        self.dem                = dem
        self.lines_layer        = lines_layer
        self.side_distance      = side_distance
        self.max_length         = max_length
        self.tolerated_a_slope  = tolerated_a_slope
        self.tolerated_c_slope  = tolerated_c_slope
        self.swath_distance     = swath_distance
        
        #Chart variables
        self.line_geom          = None
        self.aslope_list        = []
        self.c_left_slope_list  = []
        self.c_right_slope_list = []
        
        #Geometric variables
        self.edit               = False
        self.point1coord        = None
        self.point2coord        = None
        self.a_slope            = None
        self.c_left_slope       = None
        self.c_right_slope      = None
        self.length             = None
        self.max_length_hold    = max_length_hold
        
        #Rubber variables
        self.swath_display      = swath_display
        if self.swath_display == True :
            self.rub_polyline       = self.rubPolylineInit()
            self.rub_rect           = self.rubRectInit()
            self.rub_rect_anchor    = self.rubAnchorInit()
            self.rub_rect_anchors   = self.rubAnchorsInit()
            self.rub_cursor         = self.rubCursorInit()
            self.rub_buff_cursor    = self.rubBuffCursorInit()
            
        #Snap config
        self.snapper = self.snapperDef()
        return None
        
    #Event when user move the mouse : it will define a second point and launch slopeCalc function.
    def canvasMoveEvent(self,e):
        self.rub_cursor.removeLastPoint()
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        if self.max_length_hold == True and self.point1coord != None :
            pt1 = QgsPoint(self.point1coord)
            x1,y1 = self.point1coord
            pt2 = QgsPoint(point)
            dist = math.sqrt(pt1.sqrDist(pt2))
            if dist >= self.max_length :
                azimuth = pt1.azimuth(pt2)
                xv = math.sin(math.radians(azimuth))*self.max_length
                yv = math.cos(math.radians(azimuth))*self.max_length
                x2 = x1+xv
                y2 = y1+yv
                self.point2coord = QgsPoint(x2,y2)
            else :
                self.point2coord = point
        else:
            self.point2coord = point
        snap = self.snapper.snapToMap(self.point2coord)
        if snap.isValid() == True :
            x, y = snap.point()
            self.point2coord = QgsPoint(x, y)
        self.rub_cursor.removeLastPoint()
        # if self.rub_cursor.asGeometry().asPoint() == (0,0) :
        self.rub_cursor.addPoint(self.point2coord)
        # self.rub_cursor.movePoint(self.point2coord)
        
        if self.swath_display == True :
            self.rub_buff_cursor.reset()
            self.rub_buff_cursor.addGeometry(QgsGeometry.fromPoint(QgsPoint(self.point2coord[0], self.point2coord[1])).buffer(self.swath_distance,20),None)
        
        if self.point1coord != None and self.point2coord != None and self.point1coord != self.point2coord :
            self.a_slope, self.c_left_slope, self.c_right_slope, self.length = self.slopeCalc(self.point1coord, self.point2coord)
        self.callback(self.a_slope, self.c_left_slope, self.c_right_slope, self.length, self.line_geom, self.aslope_list, self.c_left_slope_list, self.c_right_slope_list, False)
        
        if self.point1coord != None and self.point2coord != None and self.point1coord != self.point2coord and self.swath_display == True :
            self.rubDisplayUp()

        return None
    
    #Event when user clicks with the mouse
    def canvasReleaseEvent(self,e):
        previousPoint = self.point1coord
        point = self.point2coord
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
                    if self.swath_display == True :
                        self.rub_rect_anchor.reset()
                        self.rub_rect_anchor.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20), None)
            else :
                pr = self.lines_layer.dataProvider()
                ids = [i.id() for i in self.lines_layer.getFeatures()]
                id = ids[-1]
                iterator = self.lines_layer.getFeatures(QgsFeatureRequest().setFilterFid(id))
                ft = next(iterator)
                geom = ft.geometry().asPolyline()
                if self.swath_display == True :
                    self.rub_rect_anchors.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20), None)
                if pr.fieldNameIndex('id') == -1 :
                    pr.addAttributes([QgsField('id', QVariant.Double,"double",6,1)] )
                    self.lines_layer.updateFields()
                id_max = 0
                for feat in self.lines_layer.getFeatures():
                    id = feat.attribute('id')
                    if id != NULL :
                        id_max = max(id_max,id)
                new_id = int(id_max) + 1
                index=self.lines_layer.fieldNameIndex("id")
                self.lines_layer.changeAttributeValue(ft.id(),index,new_id)
                self.lines_layer.commitChanges()
                self.lines_layer.startEditing()
                if pr.fieldNameIndex('length') == -1 :
                    pr.addAttributes([QgsField('length', QVariant.Double,"double",6,1)] )
                    self.lines_layer.updateFields()
                expression= QgsExpression("$length")
                index=self.lines_layer.fieldNameIndex("length")
                value = expression.evaluate(ft)
                self.lines_layer.changeAttributeValue(ft.id(),index,value)
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
                    if self.swath_display == True :
                        self.rub_rect_anchors.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20), None)
                    if pr.fieldNameIndex('id') == -1 :
                        pr.addAttributes([QgsField('id', QVariant.Double,"double",6,1)] )
                        self.lines_layer.updateFields()
                    id_max = 0
                    for feat in self.lines_layer.getFeatures():
                        id = feat.attribute('id')
                        if id != NULL :
                            id_max = max(id_max,id)
                    new_id = int(id_max) + 1
                    index=self.lines_layer.fieldNameIndex("id")
                    self.lines_layer.changeAttributeValue(ft.id(),index,new_id)
                    self.lines_layer.commitChanges()
                    self.lines_layer.startEditing()
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
    
    #When user ends a track
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
        if self.swath_display == True :
            self.rub_polyline.reset()
            self.rub_rect.reset()
            self.rub_rect_anchor.reset()
    
    #Event when user closes the plugin
    def deactivate(self) :
        if self.swath_display == True :
            self.rub_polyline.reset()
            self.rub_rect.reset()
            self.rub_rect_anchor.reset()
            self.rub_rect_anchors.reset()
            self.rub_cursor.reset()
            self.rub_buff_cursor.reset()
        self.lines_layer.updateFields()
        self.lines_layer.commitChanges()
    
    #Event when user uses 'backspace'
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
                if len(geom) > 1 :
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
                    
                    if self.swath_display == True :
                        self.rubDisplayUp()
                        #actualize rub_rect_anchor
                        self.rub_rect_anchor.reset()
                        self.rub_rect_anchor.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20),None)
                else :
                    self.lines_layer.deleteFeature(id)
                    self.reset()
                    self.canvas.refresh()
    
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
        

        return a_slope, c_left_slope, c_right_slope, dist_seg

    def rubDisplayUp(self) :
        self.rub_polyline.reset()
        self.rub_rect.reset()
        x1, y1 = self.point1coord
        x2, y2 = self.point2coord
        points = [ QgsPoint(x1,y1),QgsPoint(x2,y2)]
        self.rub_polyline.addGeometry(QgsGeometry.fromPolyline(points), None)
        if self.length < self.max_length :
            if self.a_slope < self.tolerated_a_slope and self.a_slope > -(self.tolerated_a_slope) \
                and self.c_left_slope < self.tolerated_c_slope and self.c_left_slope > -(self.tolerated_c_slope) \
                and self.c_right_slope < self.tolerated_c_slope and self.c_right_slope > -(self.tolerated_c_slope) :
                self.rub_polyline.setColor(QColor(0, 255, 0))
            else :
                self.rub_polyline.setColor(QColor(255, 0, 0))
        else :
            if self.a_slope < self.tolerated_a_slope and self.a_slope > -(self.tolerated_a_slope) and self.c_left_slope < self.tolerated_c_slope and self.c_left_slope > -(self.tolerated_c_slope) and self.c_right_slope < self.tolerated_c_slope and self.c_right_slope > -(self.tolerated_c_slope) :
                self.rub_polyline.setColor(QColor(101, 166, 101))
            else :
                self.rub_polyline.setColor(QColor(130, 54, 54))
        
        self.rub_rect.addGeometry(QgsGeometry.fromPolyline(points).buffer(self.swath_distance,20),None)
        self.rub_rect.setColor(QColor(0,255,0,50))
        return None

       
    #RUBBERBANDS INIT FUNCTIONS
    def rubAnchorsInit(self) :
        rubber = QgsRubberBand(self.canvas,True)
        
        tracks_layer = self.lines_layer
        for track in tracks_layer.getFeatures() :
            geom = track.geometry().asPolyline()
            rubber.addGeometry(QgsGeometry.fromPolyline(geom).buffer(self.swath_distance,20),None)
        rubber.setColor(QColor(0,255,0,50))
        rubber.setWidth(3)
        return rubber

    def rubAnchorInit(self) :
        rubber = QgsRubberBand(self.canvas,True)
        rubber.setColor(QColor(0,255,0,50))
        rubber.setWidth(3)
        return rubber
    
    def rubRectInit(self) :
        rubber = QgsRubberBand(self.canvas,True)
        rubber.setColor(QColor(0,255,0,50))
        rubber.setWidth(3)
        return rubber

    def rubPolylineInit(self) :
        rubber = QgsRubberBand(self.canvas,False)
        rubber.setWidth(2)
        return rubber
        
    def rubCursorInit(self) :
        rubber = QgsRubberBand(self.canvas, geometryType=0)
        rubber.setIcon(1)
        rubber.setIconSize(12)
        rubber.setWidth(2)
        rubber.setColor(QColor(235, 10, 190, 255))
        return rubber
        
    def rubBuffCursorInit(self) :
        rubber = QgsRubberBand(self.canvas,True)
        rubber.setColor(QColor(0,255,0,50))
        rubber.setWidth(3)
        return rubber
    
    #SNAP INIT FUNCTION
    def snapperDef(self) :
        snapper = QgsSnappingUtils()
        snapper.readConfigFromProject()
        snapper.setMapSettings(self.canvas.mapSettings())
        return snapper

class SelectMapTool(QgsMapTool):
    def __init__(self,iface, callback, lines_layer, dem, side_distance):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface              = iface
        self.callback           = callback
        self.canvas             = iface.mapCanvas()
        self.map_tool_name      = 'SelectMapTool'
        
        #Config variables
        self.dem                = dem
        self.lines_layer        = lines_layer
        self.side_distance      = side_distance
        
        #Chart variables
        self.line_geom          = None
        self.aslope_list        = [0]
        self.c_left_slope_list  = [0]
        self.c_right_slope_list = [0]
        
        #Geometric variables
        self.a_slope            = None
        self.c_left_slope       = None
        self.c_right_slope      = None
        self.length             = None
        
        #Rubberband init
        self.rub_polyline       = self.rubPolylineInit()
        return None
        
    def identify(self,e):
        self.reset()
        pt = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        scale = self.canvas.mapUnitsPerPixel()
        pix_tol = 10
        pt_geom = QgsGeometry().fromPoint(pt)
        pt_geom = pt_geom.buffer(scale*pix_tol,20)
        catch= False
        result= None
        geom = None
        for ft in self.lines_layer.getFeatures() :
            if pt_geom.intersects(ft.geometry()):
                result = ft
                break
        if result:
            geom = result.geometry().asPolyline()
            self.rub_polyline.addGeometry(result.geometry(),self.lines_layer)
            ln = len(geom)
            id_error_list=[]
            for i in range(0,ln-1) :
                self.a_slope, self.c_left_slope, self.c_right_slope,self.length = self.slopeCalc(geom[i],geom[i+1])
                if self.length != 0 :
                    self.aslope_list.append(math.fabs(self.a_slope))
                    self.c_left_slope_list.append(math.fabs(self.c_left_slope))
                    self.c_right_slope_list.append(math.fabs(self.c_right_slope))
                else :
                    id_error_list.append(i+1)
            if len(id_error_list) != 0 :
                for id in id_error_list :
                    del geom[id]
        if geom :
            self.callback(geom,self.aslope_list,self.c_left_slope_list,self.c_right_slope_list)
    
    def reset(self) :
        self.line_geom              = None
        self.aslope_list            = [0]
        self.c_left_slope_list      = [0]
        self.c_right_slope_list     = [0]
        self.rub_polyline.reset()
    
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
        

        return a_slope, c_left_slope, c_right_slope, dist_seg
              
    def canvasReleaseEvent(self,e):
        result = self.identify(e)
        
    def rubPolylineInit(self) :
        rubber = QgsRubberBand(self.canvas,False)
        rubber.setWidth(4)
        rubber.setColor(QColor(255, 255, 0, 255))
        return rubber