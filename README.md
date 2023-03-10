# Platoon on freeway on-ramp scenario

Welcome to the freeway off-ramp scenario project! 🔥🔥🔥  

This project aims to analyze the influence of heterogeneous platoons on the stability of traffic flow under different traffic conditions using the [SUMO](https://sumo.dlr.de/docs/index.html) + [Plexe](https://plexe.car2x.org/) simulation platform. 

## 当前进度

- [x] 异质车队: 可以设置异质车队
- [x] 车队编队：可以加入，但是考虑异质车队的插入位置还需要调整
- [ ] 车队拆分：还没做，但是只要 `plexe.remove_member(vid,LEADER)`  就可以了
- [x] 车队换道：可以自由换道，但换道只能考虑前方的障碍，不能考虑侧方向的障碍。

## Requirements

To run the simulations, we will be using the [plexe-pyapi](https://github.com/michele-segata/plexe-pyapi) interface, which provides a Python API for accessing Plexe features and functionality.

To get started with the project, you will need to install SUMO, ~~Plexe~~, and PLEXE-pyapi.
~~Manual compilation is annoying and error-prone, we recommend to using the virtual machine that comes with all the required software pre-installed in https://plexe.car2x.org/download/~~ （ It turns out that plexe-pyapi don't need Plexe or OMNet++ at all ）

### 路网导出

在OSM官网下载需要仿真的路段，下载为osm格式，修改文件后缀名为xml，

本项目选取加州91号公路 https://www.openstreetmap.org/export#map=15/33.8726/-118.0907

之后打开sumo，命令行输入netconvert转换，手动去除一些不必要的旁路之后生成随机混合交通流。

直接执行以下命令：

```shell
mv ~/Downloads/map.osm ~/Downloads/map.xml 
netconvert --osm-files ~/Downloads/map.xml --ramps.guess -o this.xml 
netedit this.xml 
```

### 添加随机交通流

查看你想要修改的参数：

```shell
python3 $SUMO_HOME/tools/randomTrips.py --help # help foe the param
```

生成随机交通流，并修正错误 https://sumo.dlr.de/docs/Tools/Trip.html

可以直接执行`cd cfg && sh autoGenTradic.sh ` 指令，参数修改注释如下：

```shell
python3 $SUMO_HOME/tools/randomTrips.py \
-n net.xml \ # 路网文件
-p 0.5 \ # 每秒生成车辆数量的倒数，越小越多
-a addition.xml \ 
--fringe-factor 1000 \ # 路网边缘产生车辆的可能性，越大越能模拟不允许随机上道的场景
-L \ # 依据车道数量产生车流量
--min-distance 1000 \
--max-distance 500000 \
--end 780 \ # 结束时间
-r output.trips1.xml \ # 生成的路网文件，
--seed 70 \ 
--validate \ # 检查可能性（死路）
--vehicle-class passenger \
--trip-attributes "maxSpeed=\"33.33333\" departSpeed=\"max\" carFollowModel=\"EIDM\"" \
--prefix passenger \ # 生成id 的前缀，用于拼合

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
--vehicle-class truck \
--trip-attributes "maxSpeed=\"23.33333\" departSpeed=\"max\" carFollowModel=\"EIDM\"" \
--prefix truck
```

~~对流进行DUA 优化，https://sumo.dlr.de/docs/Demand/Dynamic_User_Assignment.html~~

```shell
sumo-gui freeway.sumo.cfg # 预览
```

### 添加车队交通流

注意！不要改``carFollowModel="CC"`` 否则不能实现队列跟车。

```xml
          <vType id="truck0" accel="2.5" decel="8" sigma="0.5" length="9"
             minGap="6" maxSpeed="22.8" color="1,0,0" probability="1"
             carFollowModel="CC" tauEngine="0.5" omegaN="0.2" xi="1" c1="0.5" lanesCount="4" 
             vClass="truck"
            ccAccel="1.5" ploegKp="0.2" ploegKd="0.7"
             ploegH="0.5" speedFactor="2" />
添加自己的队列车辆类型：
          <vType id="truck1" accel="2.5" decel="8" sigma="0.5" length="9"
                 …… />
队列车辆的路线：（注意是edge id）
         <route id="platoon_route" edges="-gneE2 54037578 862088810 862088809 27643804 27643802#0 27643802#1-AddedOnRampEdge 27643802#1 123456265 123456270 866329792"/>

! 请注意车道的方向！
! 不能从边缘开始设置车队！，否则后车会有负的距离。
```

## Run

```shell
cd src
python3 <filename>.py
```

### 设置队列车距

```python
vtype_length = float(traci.vehicletype.getLength(VTYPE_LIST[i]))
vtyep_minGap = float(traci.vehicletype.getMinGap(VTYPE_LIST[i]))
……
add_platooning_vehicle(
            plexe,
            vid,
            position - i * (LENGTH+DISTANCE), # TODO: 动态分配，但是要注意最小车距不能小于车的长度
            LANE_NUM,
            SPEED,
            vtyep_minGap,
            real_engine,
            VTYPE_LIST[i]
        )
```

### 队列控制器

```Python
# active controller
DRIVER = 0
ACC = 1
CACC = 2
FAKED_CACC = 3
PLOEG = 4
CONSENSUS = 5

if i == 0:
            plexe.set_active_controller(vid, ACC) # 可以头车改
        else:
            plexe.set_active_controller(vid,CACC) # 不能改，否则队列就散了
```

### SpeedMode 

https://sumo.dlr.de/docs/TraCI/Change_Vehicle_State.html#speed_mode_0xb3

- bit0: Regard safe speed
- bit1: Regard maximum acceleration
- bit2: Regard maximum deceleration
- bit3: Regard right of way at intersections (only applies to approaching foe vehicles outside the intersection)
- bit4: Brake hard to avoid passing a red light
- bit5: **Disregard** right of way within intersections (only applies to foe vehicles that have entered the intersection).

```python
Python bit set:
CheckAll = 0B01111 # all 
traci.vehicle.setSpeedMode(vid, 0) # 但是没啥影响
```

### Mutiple plexe platoon flow

队列在运行中要信息交流传输，且单个队列跑完全程会让程序终止。

需要维护一个消息队列，新增车队时创建信息拓扑插入消息队列，车辆到路线末尾时先移除所属的信息拓扑，再移除所属的 plexe 车队。

### Heterogeneous vehicle types

A simple way of of modelling a heterogeneous vehicle fleet works by defining a `<vTypeDistribution>` and let each vehicle pick it's type randomly from this distribution. For details, see [vehicle type distributions](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#vehicle_type_distributions).

The python tool [createVehTypeDistributions.py](https://sumo.dlr.de/docs/Tools/Misc.html#createvehtypedistributionspy) can be used to generate large distributions that vary multiple *vType* parameters independently of each other.

> Q: where can i get detailed freeway statistic figure on vehicle flow?
>
> A:The United States Department of Transportation (USDOT) is the most comprehensive source for detailed freeway statistics. The Federal Highway Administration's website offers an online database of traffic volume maps, which includes detailed information about vehicle flow on freeways. The maps can be found at: https://www.fhwa.dot.gov/planning/tfm/traffic_volume_maps.cfm



参数; 均值+方差; 上下限

例如`car.config.txt`

```txt
tau; normal(0.8,0.1)
sigma; normal(0.5,0.2); [0,1]
length; normal(4.9,0.2); [3.5,5.5]
accel; normal(2,0.2); [1.8,2.7]
decel; normal(4,0.2); [3.6,4.4]
emergencyDecel; normal(9,0.2); [7,12]
maxSpeed; normal(50,0.2); [150,180]
param; myCustomParameter; normal(5, 2); [0, 12]
vClass; passenger
carFollowModel; IDM
```

```shell
rm vTypeDistributions.add.xml
python3 $SUMO_HOME/tools/createVehTypeDistribution.py car.config.txt --size 1000 --name "car"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py bus.config.txt --size 1000 --name "bus"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py truck.config.txt --size 1000 --name "truck"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py platoonL.config.txt --size 1000 --name "ptruck"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py platoonS.config.txt --size 1000 --name "pcar"
sed -iE 's/.000//g' vTypeDistributions.add.xml 
```

生成的`vTypeDistributions.add.xml` 是累积append 的，重新生成前要删除文件。

### 

### Heterogeneous insert state

用一系列随机函数来分配车辆的速度、路线、车道，同时符合对应的比例。

重点在于避免放置时的路线冲突。

### CACC parameters

Xi, c1 and omegaN are parameters used in the control algorithm of a Cooperative Adaptive Cruise Control (CACC) system.

- Xi is a control gain parameter that determines the level of aggressiveness in the CACC system's control strategy. A higher value of Xi means the system will be more aggressive in maintaining a constant distance from the vehicle in front. A typical value for Xi is around 0.5.
- c1 is a parameter that determines the weighting of the relative velocity error (the difference in velocity between the CACC vehicle and the vehicle in front) in the control algorithm. A higher value of c1 means the CACC vehicle will respond more strongly to changes in relative velocity. A typical value for c1 is around 0.5.
- omegaN is a parameter that determines the natural frequency of the control system's dynamics. It is used to tune the system's response to changes in velocity. A typical value for omegaN is around 1.



## Result

Once everything is installed, you can begin running the simulations by following the instructions provided in the project's documentation. You can customize the simulation by adjusting the traffic conditions and platoon configurations in the input files.

We hope that this project helps you to better understand the influence of heterogeneous platoons on traffic flow stability and helps you to optimize your traffic management strategies. Enjoy!



