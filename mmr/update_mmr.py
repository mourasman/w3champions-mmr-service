import glicko2
import numpy as np
from pydantic import BaseModel
from scipy import optimize


# ratings_G_o = all Ratings of players in Game Originally
# ratings_G_u = all Ratings of players in Game after Update
# T_G = size of a team for that Gamemode
# rds_G = rating deviations in Game

class UpdateMmrRequestBody(BaseModel):
    ratings_list: list
    rds_list: list
    t1_won: bool


class UpdateMmrResponseBody(BaseModel):
    ratings_list: list
    rds_list: list


def update_after_game(ratings_list, rds_list, T1_won):
    ratings_G = np.array(ratings_list)
    rds_G = np.array(rds_list)
    T_G = int(len(ratings_list) / 2)
    m = 60.24
    vol_4 = 0.2375
    vol_2 = 0.1195
    vol_1 = 0.06
    if T_G == 4:
        vol_p = vol_4
    elif T_G == 2:
        vol_p = vol_2
    else:
        vol_p = vol_1
    ratings_T1 = ratings_G[:T_G]
    ratings_T2 = ratings_G[T_G:]

    r_T1 = np.prod(np.power(ratings_T1, 1 / T_G))
    r_T2 = np.prod(np.power(ratings_T2, 1 / T_G))

    delta_o = (r_T1 - r_T2)

    rds_T1 = rds_G[:T_G]
    rds_T2 = rds_G[T_G:]
    rd_T1 = np.sqrt(np.sum(np.power(rds_T1, 2)))
    rd_T2 = np.sqrt(np.sum(np.power(rds_T2, 2)))

    T1 = glicko2.Player(vol=vol_p)
    T1.setRd(rd_T1)
    T1.setRating(r_T1)

    T2 = glicko2.Player(vol=vol_p)
    T2.setRd(rd_T2)
    T2.setRating(r_T1 - delta_o * T_G)

    T1.update_player([r_T1 - delta_o * T_G], [rd_T2], [T1_won])
    T2.update_player([r_T1], [rd_T1], [1 - T1_won])

    delta_u = 1 / T_G * (T1.getRating() - T2.getRating())
    xi_1 = T1.getRd() / rd_T1
    xi_2 = T2.getRd() / rd_T2
    rds_G_u = update_RD(rds_G, m, xi_1, xi_2)
    ratings_G_u = update_ratings(ratings_G, rds_G, delta_u)
    return UpdateMmrResponseBody(ratings_list=ratings_G_u.tolist(), rds_list=rds_G_u.tolist())


# function to update ratings for both teams
def update_ratings(ratings_G, rds_G, delta_u):
    res_opt = optimize.minimize(f_likelihood, x0=ratings_G,
                                args=(ratings_G, rds_G),
                                constraints={
                                    'type': 'eq',
                                    'fun': f_geomean_Delta,
                                    'args': (ratings_G, rds_G, delta_u)},
                                method='SLSQP')
    return res_opt.x


# function to update rating deviations for both teams
def update_RD(rds_G, m, xi_1, xi_2):
    T = int(len(rds_G) / 2)
    rds_T1 = rds_G[:T]
    rds_T1_u = update_RD_for_Team(rds_T1, m, xi_1)

    rds_T2 = rds_G[T:]
    rds_T2_u = update_RD_for_Team(rds_T2, m, xi_2)
    rds_G_u = np.concatenate([rds_T1_u, rds_T2_u])
    return rds_G_u


# function to update rating deviations for a team
def update_RD_for_Team(rds_T, m, xi):
    phi_T = np.sqrt(np.sum(np.power(rds_T, 2)))
    rds_T_prime = np.maximum(np.ones(len(rds_T)) * m, rds_T * xi)
    T_m = (rds_T_prime == m)
    if np.sum(T_m) > 0:
        xi_T = np.sqrt(np.sum(np.power(rds_T_prime, 2))) / phi_T
        while (np.abs(xi_T - xi) > 0.001):
            opt = optimize.minimize(f_xi_prime, 1, args=(rds_T_prime, T_m, xi, phi_T))
            xi_prime = opt.x
            rds_T_prime = np.maximum(np.ones(len(rds_T)) * m, rds_T_prime * xi_prime)
            T_m = (rds_T_prime == m)
            xi_T = np.sqrt(np.sum(np.power(rds_T_prime, 2))) / phi_T
    return rds_T_prime


# function to optimize to find xi prime
def f_xi_prime(xi_prime, rds_T, T_m, xi, phi_T):
    val = np.sqrt(np.sum(np.multiply(np.power(rds_T, 2), T_m)) + np.sum(
        np.multiply(np.power(xi_prime * rds_T, 2), (1 - T_m)))) / phi_T
    return np.abs(val - xi)


# function we are trying to minimize by constrained numerical optimization
def f_likelihood(ratings_G_u, ratings_G_o, rds_G_o):
    T_G = int(len(ratings_G_u) / 2)

    ratings_T1_u = ratings_G_u[:T_G]
    ratings_T1 = ratings_G_o[:T_G]
    r_T1 = np.prod(np.power(ratings_T1, 1 / T_G))
    r_T1_u = np.prod(np.power(ratings_T1_u, 1 / T_G))

    ratings_T2_u = ratings_G_u[T_G:]
    ratings_T2 = ratings_G_o[T_G:]
    r_T2 = np.prod(np.power(ratings_T2, 1 / T_G))
    r_T2_u = np.prod(np.power(ratings_T2_u, 1 / T_G))

    res = np.sum(np.power(np.multiply(ratings_G_u - ratings_G_o, 1 / rds_G_o), 2))
    return res


# function that defines the equality constraint of the optimization problem - this ensures that this function returns something close to '0'
def f_geomean_Delta(ratings_G_u, ratings_G_o, rds_G_o, delta_set):
    T_G = int(len(ratings_G_o) / 2)

    ratings_T1_u = ratings_G_u[:T_G]
    ratings_T1 = ratings_G_o[:T_G]
    r_T1 = np.prod(np.power(ratings_T1, 1 / T_G))
    r_T1_u = np.prod(np.power(ratings_T1_u, 1 / T_G))

    ratings_T2_u = ratings_G_u[T_G:]
    ratings_T2 = ratings_G_o[T_G:]
    r_T2 = np.prod(np.power(ratings_T2, 1 / T_G))
    r_T2_u = np.prod(np.power(ratings_T2_u, 1 / T_G))

    return (r_T1_u - r_T2_u - delta_set)

# example usage:

# update_after_game([1400, 1600, 1340, 1700, 1200, 1900, 1400, 1900], [61, 100, 100, 67, 65, 62, 63, 70], 1)
# gives
# [[1415.7225732694192,
# 1636.0959458063471,
# 1382.8216574272815,
# 1715.4833290016602,
# 1178.6338056978416,
# 1887.82309412202,
# 1382.9306817853123,
# 1884.091271066116],
# [60.25,
# 96.41497356911383,
# 96.41497356911383,
# 64.59803229130625,
# 65.65567881533067,
# 62.625416716161574,
# 63.63550408255127,
# 70.70611564727919]]

# update_after_game([1400, 1600, 1340, 1700, 1200, 1900, 1400, 1900], [61, 100, 100, 67, 65, 62, 63, 70], 0)
# gives
# [[1396.617583099109,
# 1591.2331410257361,
# 1329.5200791016296,
# 1695.7345677532749,
# 1205.629044386524,
# 1902.8675444492105,
# 1404.2116071777652,
# 1904.5643846675193],
# [60.25,
# 96.40482020086672,
# 96.40482020086672,
# 64.5912295345807,
# 65.65045914771653,
# 62.62043795628347,
# 63.63044502009449,
# 70.70049446677166]]
