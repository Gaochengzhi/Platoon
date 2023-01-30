python3 $SUMO_HOME/tools/randomTrips.py \
-n net.xml \
-p 0.01 \
--fringe-factor 100000 \
-L \
--min-distance 1000 \
--max-distance 500000 \
--end 200 \
-r output.trips1.xml \
--seed 70 \
--validate \
--vehicle-class passenger \
--trip-attributes " departSpeed=\"27\" carFollowModel=\"Krauss\" lcKeepRight=\"0\"" \
--prefix passenger \

python3 $SUMO_HOME/tools/randomTrips.py \
-n net.xml \
-p 0.03 \
--fringe-factor 100000 \
-L \
--min-distance 1000 \
--max-distance 500000 \
--end 200 \
-r output.trips2.xml \
--seed 30 \
--validate \
--vehicle-class truck \
--trip-attributes " departSpeed=\"27\" carFollowModel=\"Krauss\" lcKeepRight=\"0\"" \
--prefix truck
