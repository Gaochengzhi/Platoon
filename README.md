# Platoon on freeway off-ramp scenario 

Welcome to the freeway off-ramp scenario project! 🔥🔥🔥  


This project aims to analyze the influence of heterogeneous platoons on the stability of traffic flow under different traffic conditions using the [SUMO](https://sumo.dlr.de/docs/index.html) + [Plexe](https://plexe.car2x.org/) simulation platform. 

## Install and Run
To run the simulations, we will be using the [plexe-pyapi](https://github.com/michele-segata/plexe-pyapi) interface, which provides a Python API for accessing Plexe features and functionality.

To get started with the project, you will need to install SUMO, Plexe, and PLEXE-pyapi.
Manual compilation is annoying and error-prone, we recommend to using the virtual machine that comes with all the required software pre-installed in https://plexe.car2x.org/download/ 

### 路网导出

在OSM官网下载需要仿真的路段，下载为osm格式，修改文件后缀名为xml，

https://www.openstreetmap.org/export#map=14/29.3588/119.5952

之后打开sumo，命令行输入netconvert转换，手动去除一些不必要的旁路之后生成随机混合交通流

```shell
mv ~/Downloads/map.osm ~/Downloads/map.xml 
netconvert --osm-files ~/Downloads/map.xml --ramps.guess -o this.xml 
netedit this.xml 
```



看看你想要修改的参数：

```shell
python3 $SUMO_HOME/tools/randomTrips.py --help # help foe the param
```

生成随机交通流，并修正错误 https://sumo.dlr.de/docs/Tools/Trip.html

```shell
python3 $SUMO_HOME/tools/randomTrips.py -n this.xml -p 0.5 --fringe-factor 1 --min-distance 1000 --max-distance 500000 --end 18000 -o tripsrand.rou.xml --seed 70 --validate
```

对流进行DUA 优化，https://sumo.dlr.de/docs/Demand/Dynamic_User_Assignment.html

```
duarouter -n this.xml -t tripsrand.rou.xml -o random.rou.xml --randomize-flows true --routing-threads 10 --weights.random-factor 2 --routing-algorithm CH --ignore-errors true
```



```shell
sumo-gui freeway.sumo.cfg
```

## Result
Once everything is installed, you can begin running the simulations by following the instructions provided in the project's documentation. You can customize the simulation by adjusting the traffic conditions and platoon configurations in the input files.

We hope that this project helps you to better understand the influence of heterogeneous platoons on traffic flow stability and helps you to optimize your traffic management strategies. Enjoy!
