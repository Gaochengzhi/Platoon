#!/bin/sh

LAMBDA_VALUES="0.2 0.4 0.6"
NOISE_VALUES="3 4 5 6"
M_PRS_VALUES="0.2 0.4 0.6"
# V_SUM_VALUES="700  900  1300  1700"
V_SUM_VALUES="1100 1500"

iteration=0
core_number=12

for lambda in $LAMBDA_VALUES; do
    for noise in $NOISE_VALUES; do
        for m_prs in $M_PRS_VALUES; do
            for v_sum in $V_SUM_VALUES; do
                printf "%s %s %s %s\n" "$lambda" "$noise" "$m_prs" "$v_sum" &
                LV=$lambda NV=$noise VSUM=$v_sum MPRS=$m_prs nohup python3 main.py &
                iteration=$((iteration + 1))
                if [ "$iteration" -eq $core_number ]; then
                    sleep 3800
                    iteration=0
                fi
            done
        done
    done
done
wait

