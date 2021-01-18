from scipy import integrate
from scipy import optimize
from pydantic import BaseModel
import numpy as np

class UpdateMmrRequestBody(BaseModel):
    ratings_list: list
    rds_list: list
    T_won: int
    T: int


class UpdateMmrResponseBody(BaseModel):
    ratings_list: list
    rds_list: list

#ratings_list: ratings of all players in the game
#rds_list: rating deviations of all players in the game
#T_won: index of winning team so in [0,1] for solo/RT and in [0,1,2,3] for FFA
#T: number of teams in the game (2 for solo/RT, 4 for FFA)

def update_after_game(ratings_list, rds_list, T_won, T):
    ratings_G = np.array(ratings_list)
    rds_G = np.array(rds_list)
    
    #the whole rating system has 3 parameters:
    #(mu_0, RD_0): starting rating and deviation of (1500, 350), as we currently use - handled in the matchmaking app
    #beta: encodes performance uncertainty (this is game dependent - similar to the volatility param in Glicko2)
    #rd_min: a minimum rating deviation to prevent staleness
    beta = 215
    rd_min = 80
    
    #N: number of players in the game
    N = int(len(ratings_G))
    #maximum a posteriori to compute new ratings
    opt = optimize.minimize(lambda x: -posterior_pdf(x, ratings_G, rds_G, beta, T_won, T),
                            x0= [ratings_G])
    #updated ratings
    ratings_G_u = opt.x
    rds_G_u = []
    for p in range(N):
        #compute the normalization constant by fixing other ratings to their updated values
        #(slight approximation but alternative is a nasty (N dimensional) integration step, not feasible)
        C_int, _ = integrate.quad(lambda x: np.exp(
            posterior_pdf(np.concatenate([ratings_G_u[:p], np.array(x),ratings_G_u[p+1:]], axis=None),
                          ratings_G, rds_G, beta, T_won, T, p)),
        #integration bounds a -> b
                                  a=0,b=5000)
        #compute second moment of posterior to get new rating deviation
        #integral of p(x)*(x-mu)**2/C_int over the domain
        rd_G_u_p = np.sqrt(integrate.quad(lambda x: (x-ratings_G_u[p])**2/C_int*np.exp(posterior_pdf(np.concatenate(
            [ratings_G_u[:p], np.array(x), ratings_G_u[p+1:]], axis=None), ratings_G, rds_G, beta, T_won, T, p)),
                                          a=0, b=5000)[0])
        #floor rating deviation to prevent rating staleness
        rd_G_u_p = max(rd_min, rd_G_u_p)
        #updated rating deviations
        rds_G_u.append(rd_G_u_p)
    return UpdateMmrResponseBody(ratings_list=ratings_G_u.tolist(), rds_list=rds_G_u.tolist())


#this is faster than using the scipy.stats implementation
#(it's always the case on every project I've ever worked with, no surprises)
def logistic_pdf(x, mu, s):
    return np.exp((x-mu)/s)/(s*(1+np.exp((x-mu)/s))**2)

#this is the posterior probabiliy density function
#ratings_G_o: prior mean
#rds_G_o: prior deviation
#beta: performance uncertainty
#T_won: index of winning team
#T: number of teams in the game
#m: marginlization variable for integration purposes
def posterior_pdf(ratings_G_u, ratings_G_o, rds_G_o, beta, T_won, T, m = None):
    #N: number of players in the game
    N = int(len(ratings_G_o))
    #P: number of players per team
    P = int(float(N)/float(T))
    #constant to go from Mu/Standard deviation representation of Logistic distr. to Mu/Scale representation 
    #https://en.wikipedia.org/wiki/Logistic_distribution
    C_sd = 0.551328895
    #the game's collective rating deviation
    #each player's rating deviation is inflated by beta, which quantifies performance uncertainty
    #see https://jmlr.csail.mit.edu/papers/volume12/weng11a/weng11a.pdf
    #section 3.5, that's where I found this idea :)
    rd_G = np.sqrt(np.sum(np.power(rds_G_o,2)) + N*beta**2)
    #each team's collective rating as the geometric mean of ratings
    ratings_T_u = np.array([(np.prod(np.power(ratings_G_u[t*P:(t+1)*P], 1/float(P)))) for t in range(T)])
    #Bradley-Terry model which handles both 1 team vs 1 team and FFA
    #differs from usual BT as we have:
    #1) different rating deviation for each team
    #2) performance uncertainty with beta
    #3) multiple players by team
    s_p = np.exp((P*ratings_T_u[T_won])/(C_sd*rd_G))
    s_G =  np.sum(np.exp((P*ratings_T_u)/(C_sd*rd_G)))
    #s_p/s_G = win probability for the winning team
    #this is the evidence for the observed result
    loglikelihood = np.log(s_p/s_G)
    for n in range(N):
        #trick for the marginalization step in the integral
        if m == None or m == n:
            #this is the evidence for each player's updated rating under the prior
            loglikelihood += np.log(logistic_pdf(ratings_G_u[n], ratings_G_o[n], C_sd*rds_G_o[n]))
    return loglikelihood
