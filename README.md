# SUMO + Plexe heterogeneous platoons on highway on-ramp scenario

🚙🛣️🚦📊🔧📈🛠️

**Official code implementation** of paper *[Learning from Trajectories: How Heterogeneous CACC Platoons Affect the Traffic Flow in Highway Merging Area]()

![network copy](./assets/network%20copy.png)

This project aims to analyze the influence of heterogeneous platoons on the stability of traffic flow under different traffic conditions using the [SUMO](https://sumo.dlr.de/docs/index.html) + [Plexe](https://plexe.car2x.org/) simulation platform. 

## Requirements

To run the simulations, we will be using the [plexe-pyapi](https://github.com/michele-segata/plexe-pyapi) interface, which provides a Python API for accessing Plexe features and functionality.

### 1. Install dependencies

To get started with the project, you will need to install **SUMO, Traci, and suomlib == 1.14.1 in UNIX based machine**  and link then properly. To achieve this, the most easy way is using pip:

```shell
pip3 install eclipse-sumo==1.14.1 traci==1.14.1 sumolib==1.14.1
git clone  https://github.com/michele-segata/plexe-pyapi.git
cd plexe-pyapi
pip3 install .
```

**Any verision higher or lower than this version may causing unexpected result.**

### 2. Link to the proper version of sumo and traci

if you have installed other version of sumo, you should re link them in your host machine, otherwise you just need to update the path in your zshrc/bashrc/profile file:

```shell
export SUMO_HOME=~/.local/lib/python3.8/site-packages/sumo/
```

### 3. Error handle

**Important Note!** There should be an error when you are setting too high of a traffic density, causing spawn vehicles errors.

```shell
  File "/opt/homebrew/opt/sumo/share/sumo/tools/traci/connection.py", line 212, in _sendCmd
    packed = self._pack(format, *values)
  File "/opt/homebrew/opt/sumo/share/sumo/tools/traci/connection.py", line 166, in _pack
    packed += struct.pack("!Bb", tc.TYPE_BYTE, int(v))
struct.error: byte format requires -128 <= number <= 127
```

This is solved by modify the traci source file, like in the consloe `traci/connection.py", line 166` 

```python
>>> from this 
           elif f == "b":
                packed += struct.pack("!Bb", tc.TYPE_BYTE, int(v))
>>> into this 
           elif f == "b":
           			if v < 0 or v > max_lane_index:
           				v = random.randint(0, max_lane_index-1) // change this!!! max_lane_index is an int defined from your net settings!!! use 4 as defalut in this setting !!!
                packed += struct.pack("!Bb", tc.TYPE_BYTE, int(v))

>>> and import random in the top line.
```
** you have to ```mkdir cfg/data/``` when first start the project **

## Runing the simulation

First change your current dir into `./src`.

To run a single simulation, use the command:

```shell
LV=0.3 NV=3 VSUM=1200 MPRS=0.5 python3 main.py
```

you will get the GUI windwos below.

![Screenshot 2024-02-02 at 16.02.19](./assets/Screenshot%202024-02-02%20at%2016.02.19.jpg)

if you exit the simulation, you will get the unfinished data folder in `./src`

or if you wait utill the simulation stopped, you will get data in `./data`

To run the entire simulation, run the command in `./src/run.sh` you can change the settings based on your host machiene

```shell
#!/bin/sh

LAMBDA_VALUES="0.2 0.4 0.6"
NOISE_VALUES="3 4 5 6"
M_PRS_VALUES="0.2 0.4 0.6"
# V_SUM_VALUES="700  900  1300  1700"
V_SUM_VALUES="1100 1500"

iteration=0
core_number=12 // >> change this 

for lambda in $LAMBDA_VALUES; do
    for noise in $NOISE_VALUES; do
        for m_prs in $M_PRS_VALUES; do
            for v_sum in $V_SUM_VALUES; do
                printf "%s %s %s %s\n" "$lambda" "$noise" "$m_prs" "$v_sum" &
                LV=$lambda NV=$noise VSUM=$v_sum MPRS=$m_prs nohup python3 main.py &
                iteration=$((iteration + 1))
                if [ "$iteration" -eq $core_number ]; then
                    sleep 3800 // >> change this 
                    iteration=0
                fi
            done
        done
    done
done
wait
```

## Result analysis

To plot the fig and generate the nessasy stataical result, you can utilize the script in `./tools` folder

Or check fig in this paper in `assets/plot.sketch`
![Screenshot 2024-02-02 at 17.10.15](./assets/Screenshot%202024-02-02%20at%2017.10.15.jpg)

## Vehicle Config Generation

Vehicle conifg generate is in ./conifg file, using the command:

```shell
./geneType.sh 
```

The specific vehicle prarameters settings are in `./veh_config` folder.

The calibration process which generates thses prarameters is in another repo: https://github.com/Gaochengzhi/SUMO-calibration

![Screenshot 2024-02-02 at 16.37.33](./assets/Screenshot%202024-02-02%20at%2016.37.33.jpg)

### Road Network Config

This simulation support other map

Download the road sections needed for simulation from the OSM official website in osm format. Change the file extension to xml. 

Then open sumo and type netconvert in the command line to convert. Manually remove some unnecessary side roads and then generate random mixed traffic flow. 

You can execute the following commands:

```shell
mv ~/Downloads/map.osm ~/Downloads/map.xml
netconvert --osm-files ~/Downloads/map.xml --ramps.guess -o this.net.xml
netedit this.net.xml
```

### Random Traffic Flow

View the parameters you want to modify:

```
shellCopy code

python3 $SUMO_HOME/tools/randomTrips.py --help # help for the parameters
```

Generate random traffic flow and fix errors https://sumo.dlr.de/docs/Tools/Trip.html

You can directly execute the `cd cfg && sh autoGenTradic.sh` command. Parameter modification comments are as follows:

```shell
shellCopy code

python3 $SUMO_HOME/tools/randomTrips.py \ 
-n net.xml \ # network file
-p 0.5 \ # number of vehicles generated per second, smaller means more
-a addition.xml \  
--fringe-factor 1000 \ # possibility of generating vehicles at the edge of the network, the larger the better to simulate scenes where random access is not allowed  
-L \ # generate traffic volume according to lane quantity
--min-distance 1000 \
--max-distance 500000 \  
--end 780 \ # end time
-r output.trips1.xml \ # generated network file
--seed 70 \
--validate \ # check feasibility (dead ends)
--vehicle-class passenger \
--trip-attributes "maxSpeed=\"33.33333\" departSpeed=\"max\" carFollowModel=\"EIDM\"" \
--prefix passenger \ # prefix generated id, used for splicing

python3 $SUMO_HOME/tools/randomTrips.py \
-n net.xml \ 
-p 6 \
-a addition.xml \
--fringe-factor 1000 \ 
-L \
--min-distance 1000 \ 
--max-distance 500000 \
--end 780 \
-r output.trips2.xml \
--seed 30 \  
--validate \
--vehicle-class truck  
--trip-attributes "maxSpeed=\"23.33333\" departSpeed=\"max\" carFollowModel=\"EIDM\"" \
--prefix truck
```

