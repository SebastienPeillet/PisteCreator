# PisteCreator
ONF GUI plugins to create tracks

In French Guyana forest, it's not easy to lead engines deep into the wood. The rainy season challenges the earthworks and the tracks degrades, due to the water runoff on inclined tracks. Field operator have to plane the road access for every step in lumbering (cutting, skidding, on-site processing and trees loading onto trucks). During last decades, forestry operators tried to improve their technics to cause less environmental impact and to conform to ecolabel requirements.
This tool help to avoid tilted tracks during the tracks planification.

Qgis compatibility check :
- 2.14.12
- 2.16.0
- 2.18.3
It add a new maptool that will help the user to keep reasonable declivity when he edits the tracks layers.

## Install

Download the entire folder and copy it in the following folder :
  - `Users/.qgis2/python/plugins/`

## How to use

Input :
- tracks layer.
- DEM layer

Option dock to set :
- side distance to process cross slope (in meters)
- slope threshold (in percent) for graphic visualisation (green/red)
- maximum distance recommended (give a gray tint if overstepped)
- swath distance (length cable used on skidder in lumbering )

Left click : add a new vertice to the polyline entity.
Right click or double click : add a new vertice and end the polyline.

After you create the first vertice, the slope informations will appear into the formular when you move the cursor.
The chart gives data visualisation (with matplotlib).

## To come
- Enable snap edition
