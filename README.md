# PisteCreator
## ONF GUI plugins to create tracks

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

## Interface overview

![](http://open.geoexmachina.fr/img/article/ui_Pistecreator_en.png "interface overview")

> 1. Vector layer to edit (↻ to actualize layers)
> 2. DEM layer of the area (↻ to actualize layers)
> 3. Open the options dock
> 4. Lauch edition layer
> 5. Tool to reload the track profile
> 6. Slope values display in real time
> 7. Profile graph

## How to use :

### Input :
- tracks layer.
- DEM layer

### Option dock to set :

![](http://open.geoexmachina.fr/img/article/last_options_en.png "option dock overview")
> - Side distance to process cross slope (in meters)
> - DEM interpolation (bilinear)
> - Colors visualisation (first if slopes are OK, second otherwise)
> - Along slope threshold (in percent)
> - Cross slope threshold (in percent)
> - Maximum length recommended
> - Hold option (to avoid too long segment)
> - Colors if length exceed
> - Swath distance (length cable used on skidder in lumbering )
> - Buffer display
> - Buffer color
> - Assisted track and color display

### Tools :

#### Edit button

Enable an edit tool to create a new track with slope information and chart :
- Left click : add a new vertice to the polyline entity.
- Right click or double click : add a new vertice and end the polyline.
- Backspace : remove last point
- Escape : canceled current edition

After you create the first vertice, the slope informations will appear into the formular when you move the cursor.
The chart gives data visualisation (with matplotlib).

If assisted track option is checked, PisteCreator will proprose next segment. So, you can :
- Entry : validate the assisted track proposal
- \* : recalc for a different length (defined by the length between last point and your cursor) 

#### Select button

Enable an select tool to reload a track slope chart.

Just click on a entity to get the chart.

## To come
- Interaction with a trees layer ?
