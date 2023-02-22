#!/bin/bash
LV=(0.2 0.4 0.6)
NV=(3 4 5 6)
MPRS=(0.2 0.4 0.6)
VSUM=(1200 1600 1800)

i=0
core_num = 32

for lv in "${LV[@]}"; do
    for nv in "${NV[@]}"; do
        for mprs in "${MPRS[@]}"; do
            for vsum in "${VSUM[@]}"; do
                echo "$lv $nv $mprs $vsum" &
                LV=$lv NV=$nv VSUM=$vsum MPRS=$mprs nohup python3 main.py &
                ((i++))
                if [ "$i" -eq $core_num ]; then
                    sleep 3
                    i=0
                fi
            done
        done
    done
done
wait
