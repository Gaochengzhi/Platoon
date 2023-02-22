import itertools
import subprocess
import time

list1 = [1200, 1600, 2000]
list2 = [0.2, 0.4, 0.6]
list3 = [3, 4, 5, 6]
list4 = [0.2, 0.4, 0.6]

combinations = list(itertools.product(list1, list2, list3, list4))

running_processes = []
for combination in combinations:
    while len(running_processes) >= 32:
        for process in running_processes:
            if process:
                running_processes.remove(process)
        time.sleep(1)

    parameter1, parameter2, parameter3, parameter4 = combination
    command = f'LV={parameter3} NV={parameter2} VSUM={parameter1} MPRS={parameter4} echo "$LV $NV $VSUM $MPRS" >> tmp.txt'
    process = subprocess.run(command, shell=True)
    running_processes.append(process)
