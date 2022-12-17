python3 $SUMO_HOME/tools/randomTrips.py \
-n this.xml \
-p 0.1 \
-a addition.xml \
--fringe-factor 10000 \
--min-distance 1000 \
--max-distance 500000 \
--end 18000 \
-o output.trips1.xml \
--seed 70 \
--validate \
--vehicle-class passenger \
--trip-attributes "maxSpeed=\"33.33333\"" \
--prefix passenger

python3 $SUMO_HOME/tools/randomTrips.py \
-n this.xml \
-p 2 \
-a addition.xml \
--fringe-factor 10000 \
--min-distance 1000 \
--max-distance 500000 \
--end 18000 \
-o output.trips2.xml \
--seed 30 \
--validate \
--vehicle-class truck \
--trip-attributes "maxSpeed=\"27.78\"" \
--prefix truck
