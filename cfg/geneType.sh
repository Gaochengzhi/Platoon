rm vTypeDistributions.add.xml
python3 $SUMO_HOME/tools/createVehTypeDistribution.py car.config.txt --size 1000 --name "car"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py bus.config.txt --size 1000 --name "bus"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py truck.config.txt --size 1000 --name "truck"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py platoonL.config.txt --size 1000 --name "ptruck"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py platoonS.config.txt --size 1000 --name "pcar"
sed -iE 's/.000//g' vTypeDistributions.add.xml 
rm vTypeDistributions.add.xmlE


