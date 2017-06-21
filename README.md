# PisteCreator
ONF GUI plugins to create tracks

In French Guyana forest, it's not easy to lead engine deep into the wood. The rainy season challenges the earthworks and the tracks degrades, due to the water runoff on inclined tracks.
This tool help to avoid tilted tracks uring the tracks planification.

I developped the plugin with the 2.16.0 Qgis version, I will check for compatibilty later, for long term version (and maybe for Qgis 3 in the future). It add a new maptool that will help the user to keep reasonable declivity when he edits the tracks layers

## Install

Download the entire folder and copy it in the following folder :
  - `Users/.qgis2/python/plugins/`

## How to use

You need to enter the tracks layer and the DEM into the formular and then click on the 'Edit' button to begin edition.

A click does a vertice to te polyline entity. After you create the first vertice, the slope informations will appear into the formular when you move the cursor. A double click will ends the polyline.

## To come

- Editing attributes table during creation
- Enable snap edition
- Permit to change the distance to get elevation point on each side of the line. Default : 15 meters (Utils.py, line 150)
- Show the line that will be create before click
- probably other
