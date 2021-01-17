import numpy as np
from itertools import combinations

C_sd = 0.551328895

#this constructs the set of unique team configurations
#doing this divides by 24 from the "brute force" method that tries all possible combinations
#for footmen frenzy (3v3v3v3)
#as we go from 15400 possibilities to 369600 - it's really worth doing it as runtime goes from ~1 sec to 30 secs
#I generalized this to make it for any number of teams & number of players on the team
#this only needs to be done "once" ever - so need to make sure it's not recalculated needlessly all the time


def generate_superset_recursive(T,P):
    superset = set()
    set_players = set(i for i in range(T*P))
    potential_games = []
    for c in combinations(set_players, P):
        potential_games.append([frozenset(c)])
    L = 1
    while L<T:
        potential_games = recursion(set_players, potential_games, P)
        L+=1
    return set(frozenset(game) for game in potential_games)

def recursion(set_players, potential_games, P):
    potential_G_next = []
    for G in potential_games:
        set_players_left = set_players - set([p for team in G for p in list(team)])
        for T in combinations(set_players_left, P):
            G_T = G.copy()
            fs = frozenset(T)
            G_T.append(fs)
            potential_G_next.append(G_T)
    return potential_G_next

#this gives the winning odds for each team for configuration of the game
def game_odds(ratings_G, rds_G, T, P):
    #should be hardcoded to the same value as in the python mmr service
    beta = 215
    #number of players per game
    N = len(rds_G)
    rd_G = np.sqrt(np.sum(rds_G**2)+N*beta**2)
    ratings_T = np.array([(np.prod(np.power(ratings_G[t*P:(t+1)*P], 1/float(P)))) for t in range(T)])
    odds = np.exp((P*ratings_T)/(C_sd*rd_G))/np.sum(np.exp((P*ratings_T)/(C_sd*rd_G)))
    return odds


#gamemode should be of the form "PvPvP" or "PonPonP"
#number of teams is occurences of "v"+1

def find_best_game(ratings, rds, gamemode):
    #that part should be refactored by someone who understands
    #what variables will remain in memory on the live service
    #the point is that generaate_super_recursive should only be called once per gamemode
    #whenever we restart the service
    #and its output be available in memory at any time later
    T = gamemode.count(gamemode[0])
    P = int(gamemode[0])
    if 'superset' not in globals():
        global superset
        superset = {}
        superset[gamemode] =generate_superset_recursive(T, P)
    else:
        if gamemode not in superset.keys():
            superset[gamemode] = generate_superset_recursive(T, P)
    gamemode_set = superset[gamemode]
    most_fair = 1
    for Game in gamemode_set:
        potential_G = [p for Team in Game for p in Team]
        ratings_G = ratings[potential_G]
        probas = game_odds(ratings_G, rds_G, T, P)
        #that's helpstone's metric for a fair game
        fairness_G = np.max(probas) - np.min(probas)
        if fairness_G < most_fair:
            best_G = potential_G
            best_ratings = ratings_G
            most_fair = fairness_G
    return [int(np.ceil((best_G.index(p)+1)/P)) for p in range(T*P)]

# #Example usage
# ratings_G = np.round(np.random.normal(1500, 300, 12),0)
# print(ratings_G)
# rds_G = np.array([90]*12)
# teams_footies = find_best_game(ratings_G, rds_G, '3v3v3v3')
# print(teams_footies)


# ratings_G = np.round(np.random.normal(1500, 300, 8),0)
# print(ratings_G)
# rds_G = np.array([90]*8)
# teams_4s = find_best_game(ratings_G, rds_G, '4v4')
# print(teams_4s)
