import copy
import os
import math
import matplotlib.pyplot as plt
import numpy as np


# EIDM Parameter
# desire speed


N = int(os.environ["n"])
p_truck = os.environ["truck"]
fig = plt.gcf()
fig.set_size_inches(4, 3)
fig.set_dpi(800)


def fdx_cacc(tc):
    kp = 0.45
    kd = 0.25
    dt = 0.01
    fdx_cacc = kp / (dt + kd * tc)
    return fdx_cacc


def f_value_cacc(tc=0.5):
    kp = 0.45
    kd = 0.25
    dt = 0.01
    return kp / (kd * tc + dt)


def f_v_idmi(v_0, s_0, v, a_max, Ti):
    term1 = -4 * a_max * (v**3) / (v_0**4)
    term2 = -2 * a_max * Ti * (1 - ((v / v_0) ** 4)) / (s_0 + v * Ti)
    return term1 + term2


def f_deltav_idmi(v_0, s_0, v, a_max, b, Ti):
    term1 = (a_max / b) ** (1 / 2)
    term2 = v * (1 - (v / v_0) ** 4) / (s_0 + v * Ti)
    return term1 * term2


def f_deltax_idmi(v_0, s_0, v, a_max, Ti):
    term1 = 2 * a_max * ((1 - (v / (v_0 + 0.001)) ** 4) ** (3 / 2))
    term2 = s_0 + v * Ti
    return term1 / term2


def f_value_idmi(v_0, s_0, v, a_max, b, Ti):
    f_v = f_v_idmi(v_0, s_0, v, a_max, Ti)
    f_deltav = f_deltav_idmi(v_0, s_0, v, a_max, b, Ti)
    f_deltax = f_deltax_idmi(v_0, s_0, v, a_max, Ti)
    f_value = (f_v**2) / 2 - f_deltav * f_v - f_deltax
    return f_value


def gen_rand_array(mean, std, min, max):
    np.random.seed(np.random.randint(0, 10))
    arr = []
    while len(arr) < 3000:
        vals = np.random.normal(mean, std, 3000)
        vals = np.clip(vals, min, max)
        arr.extend(vals)
    arr = arr[:3000]
    return arr


def get_f_value(p_truck=0.5):
    car_acc = gen_rand_array(2.5, 2, 2.0, 3.5)
    car_dec = gen_rand_array(5, 2, 4.5, 5.5)
    car_tau = gen_rand_array(1.5, 1, 1.3, 1.7)
    car_s = gen_rand_array(3, 1, 2.5, 3.5)
    car_v = gen_rand_array(36, 4.7, 33, 45)

    truck_acc = gen_rand_array(1.2, 2, 1.0, 1.4)
    truck_dec = gen_rand_array(3, 2, 2.6, 3.4)
    truck_tau = gen_rand_array(2.1, 1, 1.6, 2.6)
    truck_s = gen_rand_array(4.5, 1, 4.0, 5.7)
    truck_v = gen_rand_array(27, 1.9, 26, 28)
    # cacc_car_tau = gen_rand_array(0.5, 0.1, 0.4, 0.6)
    # cacc_truck_tau = gen_rand_array(0.7, 0.1, 0.4, 0.9)

    v_range = np.arange(0.1, 33, 0.3)
    p_range = np.arange(0.1, 1, 0.01)

    ff_value = []
    # ff_value.clear()
    for p_cacc in p_range:
        ff_p_value = []
        ff_p_value.clear()

        reslist = []
        reslist.clear()
        for v in v_range:
            res = 0
            car_f_value = []
            car_headway_list = []

            truck_f_value = []
            truck_headway_list = []

            cacc_f_value = []
            cacc_headway_list = []

            car_type_len = int(3000 * (1 - p_truck) * (1 - p_cacc))
            for i in range(car_type_len):
                f_value_cari = f_value_idmi(
                    car_v[i], car_s[i], v, car_acc[i], car_dec[i], car_tau[i]
                )
                car_headway = f_deltax_idmi(
                    car_v[i], car_s[i], v, car_acc[i], car_tau[i]
                )
                car_f_value.append(f_value_cari)
                car_headway_list.append(car_headway)
                pass

            truck_type_len = int(3000 * (p_truck) * (1 - p_cacc))
            for i in range(truck_type_len):
                f_value_trucki = f_value_idmi(
                    truck_v[i], truck_s[i], v, truck_acc[i], truck_dec[i], truck_tau[i]
                )
                truck_headway = f_deltax_idmi(
                    truck_v[i], truck_s[i], v, truck_acc[i], truck_tau[i]
                )
                truck_f_value.append(f_value_trucki)
                truck_headway_list.append(truck_headway)
                pass

            cacc_type_len = int(3000 * (p_cacc))
            for i in range(cacc_type_len):
                fvalue_cacc = f_value_cacc()
                cacc_headway = fdx_cacc(0.5)
                cacc_f_value.append(fvalue_cacc)
                cacc_headway_list.append(cacc_headway)
                pass

            for i in range(car_type_len + truck_type_len + cacc_type_len):
                if i < car_type_len:
                    else_headway = car_headway_list
                    this_type_car_headway = else_headway[i]
                    car_ff_value = (
                        (1 - p_truck)
                        * (1 - p_cacc)
                        / car_type_len
                        * car_f_value[i]
                        / (this_type_car_headway**2)
                    )
                    ff_p_value.append(car_ff_value)

                elif i < car_type_len + truck_type_len:
                    else_headway = truck_headway_list
                    this_type_truck_headway = else_headway[i - car_type_len]

                    truck_ff_value = (
                        (p_truck)
                        * (1 - p_cacc)
                        / truck_type_len
                        * truck_f_value[i - car_type_len]
                        / (this_type_truck_headway**2)
                    )
                    ff_p_value.append(truck_ff_value)
                else:
                    else_headway = cacc_headway_list
                    this_type_cacc_headway = else_headway[
                        i - car_type_len - truck_type_len
                    ]
                    cacc_ff_value = (
                        (p_cacc)
                        / (N * cacc_type_len)
                        * cacc_f_value[i - car_type_len - truck_type_len]
                        / (this_type_cacc_headway**2)
                    )
                    ff_p_value.append(cacc_ff_value)

                    tmp = fdx_cacc(0.1)
                    cacc_ff_value2 = (
                        p_cacc
                        * (N - 1)
                        / (N * cacc_type_len)
                        * f_value_cacc(0.1)
                        / (tmp**2)
                    )
                    ff_p_value.append(cacc_ff_value2)

            res = np.sum(ff_p_value)
            reslist.append(res)
        ff_value.append(reslist)

    return ff_value


def plot_f_value():
    data = get_f_value(float(p_truck))
    for i in range(len(data)):
        pass
    plt.imshow(data, origin="lower", cmap="gist_ncar")
    plt.clim(-10, 20)
    plt.xlabel("Velocity (km/h)")
    plt.ylabel("CACC MPR")
    plt.title(f"CACC size: {N} truck ratio: {p_truck[2]}0%")
    plt.colorbar(label='FF',orientation='vertical')
    curves = 1
    m = max([max(row) for row in data])
    levels = np.arange(0, m, (1 / float(curves)) * m)
    plt.contour(data, linewidths=0.8, colors="black", levels=levels)
    # plt.show()
    plt.savefig(f"ff_value_N{N}_truck{p_truck}.png", dpi=300,bbox_inches='tight', pad_inches=0.08)


def main():
    plot_f_value()
    pass


if __name__ == "__main__":
    main()

