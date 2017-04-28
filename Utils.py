# -*- coding: utf-8 -*-
"""
***************************************************************************
 Slope_road
								 A QGIS plugin
 Tools to calculate along and cross slope for road
							  -------------------
		begin				 : 2017-03-22
		git sha				 : 2017-03-29:16
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
import math

class SlopeMapTool(QgsMapTool):
    def __init__(self,iface, callback, dem):
        QgsMapTool.__init__(self,iface.mapCanvas())
        self.iface      = iface
        self.callback   = callback
        self.canvas     = iface.mapCanvas()
        # self.trackslayer = trackslayer
        self.dem = dem
        self.points = []
        self.point1coord= None
        self.point2coord= None
        self.aSlope= None
        self.cSlope= None
        return None
        
    def canvasMoveEvent(self,e):
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(),e.pos().y())
        self.point2coord = point
        if self.point1coord != None and self.point2coord != None and self.point1coord!=self.point2coord :
            self.aSlope,self.cSlope = self.slopeCalc(self.point1coord,self.point2coord)
        self.callback(self.aSlope,self.cSlope)
        return None
        
    def canvasReleaseEvent(self,e):
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(),e.pos().y())
        self.point1coord = point
        #add vertices
        self.callback(self.aSlope,self.cSlope)
        return None

    # def canvasPressEvent(self,e):
        # point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(),e.pos().y())
        # #self.points.append(point)
        # self.callback(point)
        # return None
    def coordPoint(self,Point) :
        x1,y1=Point
        return x1
    def slopeCalcTest(self,sP,eP):
        x1,y1=sP
        x2,y2=eP
        return x1,x2
        
    # def reset(self):
        # self.startPoint = self.endPoint = None
        # self.isEmittingPoint = False
    
    def slopeCalc(self, sP, eP) :
        # #Retrieve coord
        x1,y1=sP
        x2,y2=eP
        
        # Along slope calculation
        zStartIdent = self.dem.dataProvider().identify(sP,QgsRaster.IdentifyFormatValue)
        zStartValue = zStartIdent.results()[1]
        zEndIdent = self.dem.dataProvider().identify(eP,QgsRaster.IdentifyFormatValue)
        zEndValue = zEndIdent.results()[1]
        distSeg=math.sqrt(sP.sqrDist(eP))

        if (zStartValue != None and zEndValue != None and distSeg != 0) :
            aSlope=math.fabs(zStartValue-zEndValue)/distSeg*100
        else :
            aSlope=None
        
        # Along slope calculation
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
        dist=15
        #vecteur directeur buff
        Xv= dist*math.cos(math.radians(angle))
        Yv= dist*math.sin(math.radians(angle))
        #point buff
        x_pointleft=xc-Xv
        y_pointleft=yc+Yv
        x_pointright=xc+Xv
        y_pointright=yc-Yv
        pointleft = QgsPoint(x_pointleft,y_pointleft)
        zLeftIdent = self.dem.dataProvider().identify(pointleft,QgsRaster.IdentifyFormatValue)
        zLeftValue = zLeftIdent.results()[1]
        pointright = QgsPoint(x_pointright,y_pointright)
        zRightIdent = self.dem.dataProvider().identify(pointright,QgsRaster.IdentifyFormatValue)
        zRightValue = zRightIdent.results()[1]
        if (zLeftValue != None and zRightValue != None and dist!=0) :
            cSlope=math.fabs(zLeftValue - zRightValue)/(dist*2)*100
        else :
            cSlope=None
        return aSlope , cSlope


