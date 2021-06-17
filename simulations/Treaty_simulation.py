import numpy as np
import pandas
from math import isclose
from Treaty_game_model import ie, pd, dp

class Treaty:
    def __init__(self, s_efficiency, a, b, c, d, e, noise_sd, 
                 annuity_payment=1/2, lumpsum_payment=1.5):
        self.a, self.b, self.c, self.d, self.e = a, b, c, d, e
        self.s_efficiency = s_efficiency
        self.noise_sd = noise_sd
        self.annuity_payment = annuity_payment
        self.lumpsum_payment = lumpsum_payment
        
    def propose_treaty(self, s_land, s_spending):
        a, b, c = self.a, self.b, self.c
        noise = np.random.normal(scale=self.noise_sd)
        exp = np.exp(c -a*s_spending - b*(100-s_land) + noise )
        return 1/(1 + exp)
    
    def content_treaty(self, s_land, total_treaty_benefits, s_savings,
                       treaty_type='annuity'):
        land_choices = np.arange(50, self.s_efficiency+1) 
        s_treaty_land = np.random.choice(land_choices, p=land_choices/np.sum(land_choices))
        if treaty_type == 'annuity':
            transfer = self.annuity_payment * total_treaty_benefits
        else:
            transfer =  self.lumpsum_payment * total_treaty_benefits
        if transfer > s_savings:
            transfer = s_savings
        return s_treaty_land, transfer
    
    def accept_treaty(self):
        return 1
    
    def end_treaty(self, s_treaty_land):
        noise = np.random.normal(scale=self.noise_sd)
        exp = np.exp(self.e - self.d*(100 - s_treaty_land) + noise)
        p_settler_ending = 1/(1+exp)
        p_native_ending = np.random.uniform(0, 0.4)
        return p_settler_ending, p_native_ending

def TotalTreatyBenefits(n_land, n_spending, s_spending):
    global_income_change = ie.TotalIncome(100-ie.global_efficiency) - ie.TotalIncome(n_land)
    saving_fighting = n_spending + s_spending
    return global_income_change + saving_fighting

def TreatyEndingReason(draw_s_ending, draw_n_ending, s_ending, n_ending):
    if draw_s_ending > s_ending and draw_n_ending > n_ending:
        return 'ContinueTreaty'
    elif draw_s_ending <= s_ending and draw_n_ending <= n_ending:
        return 'BothBroken'
    elif draw_s_ending <= s_ending:
        return 'SettlerBroken'
    else:
        return 'NativeBroken'

def SpendingExpansion(n_land, current_period, spending_shock, n_savings, s_savings, spending_shock_size):
    spendings, responses = dp.ResponseList(n_land, current_period)
    eq_spending = dp.FindNE(spendings, responses)
    if spending_shock:
        eq_spending = dp.SpendingShocks(spendings[0][-1], eq_spending[0], 
                                        spendings[1][-1], eq_spending[1], 
                                        spending_shock_size)
    n_spending, s_spending = eq_spending 
    n_savings -= n_spending
    s_savings -= s_spending
    n_land_diff = dp.IfEqSpending(n_land, eq_spending, simulation=True)
    return n_spending, s_spending, n_savings, s_savings, n_land_diff

def TreatySavingsChange(n_savings, s_savings, n_land, s_treaty_land, transfer, treaty_type):
    if not isclose(n_land + s_treaty_land, 100):
        raise ValueError('Check land split of the treaty!')
    if treaty_type == 'annuity':
        n_savings += ie.NativeIncome(n_land) + transfer
        s_savings += ie.SettlerIncome(s_treaty_land) - transfer
    else:
        n_savings += ie.NativeIncome(n_land)
        s_savings += ie.SettlerIncome(s_treaty_land)
    return n_savings, s_savings
        
def TreatySimulation(n_land_start, tr,
                     treatment,
                     max_periods = 20, 
                     matches=100, 
                     endowments=100,
                     spending_shock=True,
                     spending_shock_size=(0, 2)):
    match_obs = []
    for match in range(1, matches+1):
        treaty_type = treatment
        #treaty_type = np.random.choice(['annuity', 'lumpsum'], p=[1/2, 1/2])
        tot_periods = min(max_periods, np.random.geometric(pd.prob))
        n_savings_init = s_savings_init = endowments
        current_period = 1
        have_treaty = False
        n_land_init = n_land_start
        while current_period <= tot_periods:
            n_income = ie.NativeIncome(n_land_init) # pure income change without fighting
            s_income = ie.SettlerIncome(100 - n_land_init)
            n_savings_end = n_savings_init + n_income
            s_savings_end = s_savings_init + s_income
            if current_period >= 2 and match_obs[-1][-1] == None:
                prob_tr = tr.propose_treaty(100-n_land_init, s_spending)
                if np.random.random() < prob_tr:  # propose a treaty
                    total_treaty_benefits = TotalTreatyBenefits(n_land_init, n_spending, s_spending)
                    s_treaty_land, transfer = tr.content_treaty(100-n_land_init, total_treaty_benefits,
                                                            s_savings_end, treaty_type)   # treaty content
                    if np.random.random() < tr.accept_treaty(): # accept a treaty
                        n_land_end = 100 - s_treaty_land
                        n_savings_end += transfer
                        s_savings_end -= transfer
                        have_treaty = True
                        while current_period <= tot_periods:
                            obs = [match, current_period, 0, 0, n_savings_init, n_savings_end, s_savings_init, s_savings_end, 
                                   n_land_init, n_land_end, 100-n_land_init, 100-n_land_end, n_income, s_income, treaty_type, transfer, None]
                            match_obs.append(obs)
                            n_income = ie.NativeIncome(n_land_end)
                            s_income = ie.SettlerIncome(s_treaty_land)
                            current_period += 1
                            if current_period > tot_periods:
                                match_obs[-1][-1] = 'MatchEnding'
                                break
                            draw_s_ending, draw_n_ending = np.random.random(2)
                            s_ending, n_ending = tr.end_treaty(s_treaty_land)
                            treaty_status = TreatyEndingReason(draw_s_ending, draw_n_ending, s_ending, n_ending)
                            if treaty_status == 'ContinueTreaty':
                                match_obs[-1][-1] = 'ContinueTreaty'
                                pass
                            elif treaty_status == 'BothBroken':
                                match_obs[-1][-1] = 'BothBroken'
                                break
                            elif treaty_status == 'SettlerBroken':
                                match_obs[-1][-1] = 'SettlerBroken'
                                break
                            elif treaty_status == 'NativeBroken':
                                match_obs[-1][-1] = 'NativeBroken'
                                break
                            n_savings_init = n_savings_end
                            s_savings_init = s_savings_end
                            n_land_init = n_land_end
                            n_savings_end, s_savings_end = TreatySavingsChange(n_savings_init, s_savings_init, n_land_init, s_treaty_land, transfer, treaty_type)
                        if have_treaty and match_obs[-1][-1] != None and current_period <= tot_periods:
                            have_treaty = False
                            n_savings_init = n_savings_end
                            s_savings_init = s_savings_end
                            n_savings_end = n_savings_init + n_income
                            s_savings_end = s_savings_init + s_income
                            n_land_end = n_land_init
                            obs = [match, current_period, 0, 0, n_savings_init, n_savings_end, s_savings_init, s_savings_end, 
                                   n_land_init, n_land_end, 100-n_land_init, 100-n_land_end, n_income, s_income, np.nan, np.nan, None]
                            match_obs.append(obs)
                            current_period += 1
                            n_savings_init = n_savings_end
                            s_savings_init = s_savings_end
                            n_savings_end = n_savings_init + n_income
                            s_savings_end = s_savings_init + s_income
                            n_land_init = n_land_end
                    else:
                        pass
                else:
                    pass
            else:
                pass  
            if (current_period <= tot_periods) and (current_period == 1 or not have_treaty):
                n_spending, s_spending, n_savings_end, s_savings_end, n_land_diff = SpendingExpansion(
                    n_land_init, current_period, spending_shock, n_savings_end, s_savings_end, spending_shock_size)  # fighting results
                n_land_end = n_land_init + n_land_diff
                obs = [match, current_period, n_spending, s_spending, n_savings_init, n_savings_end, s_savings_init, 
                       s_savings_end,  n_land_init, n_land_end, 100-n_land_init, 100-n_land_end, n_income, s_income, np.nan, np.nan, None]
                                                                    # treaty_type, transfer, treaty_num, broken_reason
                current_period += 1
                n_land_init = n_land_end
                n_savings_init = n_savings_end
                s_savings_init = s_savings_end
                match_obs.append(obs)
    cols = ['Match', 'CurrentPeriod', 'NativeSpending', 'SettlerSpending', 'InitNativeSaving', 'EndNativeSaving', 'InitSettlerSaving', 'EndSettlerSaving', 
            'InitNativeLand', 'EndNativeLand', 'InitSettlerLand','EndSettlerLand', 'NativeIncome','SettlerIncome', 'TreatyType', 'TreatyPayment', 'TreatyEndingReason']
    simulated_data = pandas.DataFrame(data=match_obs,  columns=cols)
    return simulated_data

n_subs = 50
all_data = []
for i in range(1, n_subs+1):
    mean = [1/20, 1/30, 0, 1/25, 2]
    cov = np.diag([0.2, 0.1, 1, 0.1, 0.2])
    a, b, c, d, e = np.random.multivariate_normal(mean=mean, cov=cov)
    tr = Treaty(ie.global_efficiency, a, b, c, d, e, 2)
    treatment = np.random.choice(['annuity', 'lumpsum'], p=[1/2, 1/2])
    data = TreatySimulation(65, tr, treatment, matches=4)
    data.insert(0, 'SubId', 100+i)
    all_data.append(data)
res = pandas.concat(all_data)
res.to_csv('SimulatedData.csv', index=False,  float_format='%.0f')

