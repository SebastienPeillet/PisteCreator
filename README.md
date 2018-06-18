
# PisteCreator <img src="http://open.geoexmachina.fr/img/article/PC_icon.png"></img>
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

![](http://open.geoexmachina.fr/img/article/ui_Pistecreator_v1_7.PNG "interface overview")

> 1. Vector layer to edit
> 2. DEM layer of the area
> 3. Assisted mode option
> 4. Open the options dock
> 5. Lauch edition layer
> 6. Tool to reload the track profile
> 7. Slope values display in real time
> 8. Profile graph

## How to use :

### Input :
- tracks layer.
- DEM layer

### Option dock to set :
Option dock changes with the selected assisted mode. If "Inactive" or "Skidding Track" are set, the full option dock will appear.

![](http://open.geoexmachina.fr/img/article/panneau_option_1.PNG "option dock overview")
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

With the "Truck track" assisted mode, there is a few options less. For example the cross slope is not so useful anymore because of earthworks which are needed for this type of road.

![](http://open.geoexmachina.fr/img/article/panneau_option_2.PNG "option dock overview")
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

There is two assisted mod. 

The "**Truck track**" mode is made to pass through mountainous relief. This type of road will need earthworks to prevent cross slope, but to avoid them as much as we can, this mode will propose the steepest allowed segment.

Example:

![](http://open.geoexmachina.fr/img/article/test_assiste.gif "truck track mode")

The "**Skidding track**" mode is made for end track network. This type of track are used to reach trunks. This doesn't need earthwork, so we have to be more cautious on cross slope. This mode will provided a cone area that fits with the slope parameters. The operateur just have to click in the cone. In this way, it's also possible to deviate to reach a neighbour trunk.

Example :

![](http://open.geoexmachina.fr/img/article/test_assiste_clois.gif "truck track mode")
*Points are identified trees*

#### Select button

Enable an select tool to reload a track slope chart.

Just click on a entity to get the chart.

## To come
- Interaction with a trees layer ?
