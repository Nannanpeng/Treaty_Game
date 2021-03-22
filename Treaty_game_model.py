### Code to solve the treaty game ###

import numpy as np
from scipy.optimize import fminbound
import matplotlib.pyplot as plt
import time

class GraphPlot:
    def __init__(self, begin, end, grids):
        self.xvalues = np.linspace(begin, end, grids)
        
    def IncomeGraph(self, yvalues_list, xlabel = 'Land', ylabel = 'Profit'):
        fig, ax = plt.subplots(figsize = (9, 6))
        ax.set(title = str(xlabel) + ' v.s. ' + str(ylabel), xlabel = str(xlabel), ylabel = str(ylabel))
        labels = ['Native', 'Settler', 'Total']
        for i in range(len(yvalues_list)):
            ax.plot(self.xvalues, yvalues_list[i], labeL = labels[i])
        ax.legend()
        ax.grid()
        plt.show()
        
    def CostProfit(self, yvalues, xlabel = 'Land', ylabel = 'Income/cost'):
        fig, ax = plt.subplots(figsize = (9, 6))
        ax.set(title = str(xlabel) + ' v.s. ' + str(ylabel), xlabel = str(xlabel), ylabel = str(ylabel))
        labels = ['Native_MI', 'Settler_MI', 'Native_MC', 'Settler_MC']
        for i in range(len(yvalues)):
            ax.plot(self.xvalues, yvalues[i], label=labels[i])
        ax.grid()
        ax.legend()
        plt.show()  
        
    def LandChange(self, yvalues, xlabel = 'Period', ylabel = 'Land'):
        fig, ax = plt.subplots(figsize = (9, 6))
        ax.set(title = str(ylabel) + ' v.s. ' + str(xlabel), xlabel = str(xlabel), ylabel = str(ylabel))
        labels = ['Native', 'Settler']
        for i in range(len(yvalues)):
            ax.plot(yvalues[i], label=labels[i])
#        ax.set(ylim=(0, 25), xlim=(1, 100))
        ax.grid()
        ax.legend()
        plt.show()  
        
    def BestResponse(self, xvalues, yvalues, eq_spending): #[n_income_list, s_income_list], [s_best_spending, n_best_spending]
        fig, ax = plt.subplots(figsize = (9, 6))
        ax.set(title = 'Best Spending Decision', xlabel = 'Native', ylabel = 'Settler')        
        labels = ['Settler', 'Native']
        ax.plot(xvalues[0], yvalues[0], label=labels[0])
        ax.plot(yvalues[1], xvalues[1], label=labels[1])
        ax.plot(eq_spending[0], eq_spending[1], 'ro')
        ax.grid()
        ax.legend()
        plt.show() 

class IncomeExpansion:
    '''
    A set of basis functions describing player's behavior.
    
    Parameters:
    ----------
    All parameters are float.
    A1, B1, C1 (A2, B2, C2): Native's (Settler's) income params.
    D, H: Native and Settler's expansion params.
    gamma: Additional params for Native's expansion.
    H, beta: Additional params for Settler's expansion.

    '''
    def __init__(self, A1, B1, C1, A2, B2, C2, D, E, H, gamma, beta):
        self.A1, self.B1, self.C1 = A1, B1, C1
        self.D, self.E, self.H, self.gamma, self.beta = D, E, H, gamma, beta
        self.A2, self.B2, self.C2 = A2, B2, C2
        
    def NativeIncome(self, land):
        A1, B1, C1 = self.A1, self.B1, self.C1
        return  A1/(1+ np.exp(-B1* (land - C1))) - A1/(1+ np.exp(B1 * C1))

    def SettlerIncome(self, land):
        A2, B2, C2 = self.A2, self.B2, self.C2 
        return A2/(1+ np.exp(-B2* (land - C2))) - A2/(1+ np.exp(B2 * C2)) 

    def NativeExpan(self, spending, land):
        D, H, gamma = self.D, self.H, self.gamma
        return  spending**(1 - gamma)/(land + D) * (H - land)
 
    def SettlerExpan(self, spending, land):
        D, E, H, beta = self.D, self.E, self.H, self.beta
        return  spending**(1 - beta)/(land + D + E) * (H - land)


class PlayerDecision:
    '''
    Several functions calculating player's reponse and profit.
    
    Parameters:
    ---------
    IE: IncomeExpansion instance.
    prob: probability to end the game in each period.
    n_default: default periods without uncertainty at the begining of the game.
    '''
    def __init__(self, IE, prob, n_default):
         self.ie = IE
         self.periods = int((1 - prob)/prob)
         self.n_dft = n_default
         
    def NativeProfit(self, land, n_spending, s_spending, current_p):
         land_diff = self.ie.NativeExpan(n_spending, land) - self.ie.SettlerExpan(s_spending, 100-land)
         revenue =  self.ie.NativeIncome(land + land_diff) - self.ie.NativeIncome(land)
         if current_p <= self.n_dft:
             n_profit = revenue * (self.n_dft - current_p + self.periods) - n_spending
         else:
             n_profit = revenue * self.periods - n_spending
         return n_profit
     
    def NativeResponse(self, land, s_spending, current_p):
         income = self.ie.NativeIncome(land)
         Sfun = lambda n_spending: self.NativeProfit(land, n_spending, s_spending, current_p)
         return fminbound(lambda s: -Sfun(s), 0, income)
     
    def SettlerProfit(self, land, n_spending, s_spending, current_p):
         land_diff = self.ie.SettlerExpan(s_spending, land) - self.ie.NativeExpan(n_spending, 100 - land)
         revenue =  self.ie.SettlerIncome(land + land_diff) - self.ie.SettlerIncome(land)
         if current_p <= self.n_dft:
             s_profit = revenue * (self.n_dft - current_p + self.periods) - s_spending
         else:
             s_profit = revenue * self.periods - s_spending
         return s_profit
     
    def SettlerResponse(self, land, n_spending, current_p):
         income = self.ie.SettlerIncome(land)
         Sfun = lambda s_spending: self.SettlerProfit(land, n_spending, s_spending, current_p)
         return fminbound(lambda s: -Sfun(s), 0, income)
     
class DP:
    '''
    Dynamic programming figuring out the best response of each player.
    
    Parameters:
    ----------
    IE: IncomeExpansion instance:
    PD: PlayerDecision instance.
    '''
    def __init__(self, IE, PD):
         self.ie, self.pd = IE, PD
    def ResponseList(self, n_land, current_p, n_savings=None, s_savings=None, saving=False):
         n_income = self.ie.NativeIncome(n_land)
         s_income = self.ie.SettlerIncome(100 - n_land)
         if not saving:
             n_spending_list = np.linspace(0, n_income, 250)
             s_spending_list = np.linspace(0, s_income, 250)
         else:
             n_spending_list = np.linspace(0, n_income+n_savings, 500)
             s_spending_list = np.linspace(0, s_income+s_savings, 500)
         n_best_spending = []
         s_best_spending = []
         for s_spending in s_spending_list:
             n_best_spending.append(self.pd.NativeResponse(n_land, s_spending, current_p))
         for n_spending in n_spending_list:
             s_best_spending.append(self.pd.SettlerResponse(100 - n_land, n_spending, current_p))
         return [n_spending_list, s_spending_list], [s_best_spending, n_best_spending]
     
    def FindNE(self, income_list, spending_list): #[n_spending_list, s_spending_list], [s_best_spending, n_best_spending]
         for s_spending in spending_list[0]:
             s_index = (np.abs(np.array(income_list[1]) - s_spending)).argmin() #index for settler spending/native best response
             n_spending = spending_list[1][s_index]
             n_index = (np.abs(np.array(income_list[0]) - n_spending)).argmin() #index for  native spending/settler best response
             if abs(spending_list[0][n_index] - s_spending) < 0.01:
                 return [n_spending, s_spending] 
             else:
                 pass
     
    def IfEqSpending(self, n_land, eq_spending, tol=1e-4, simulation=False): # [n_spending, s_spending] 
         diff = self.ie.NativeExpan(eq_spending[0], n_land) - self.ie.SettlerExpan(eq_spending[1], 100 - n_land)
         if not simulation:
             return 'pass' if abs(diff) < tol else diff
         else:
             return diff
     
    def DynamicNE(self, n_land, saving=False, max_iter=300, verbose=True): #[n_income_list, s_income_list], [s_best_spending, n_best_spending]
         '''
         Take the intial land of Native. Return native and settler's best spending, native's land  and spe_res.
         
         Parameters:
         ----------
             n_land (float): Native's land.
         '''
         spe_res, ns_best_spending, n_land_list = [], [], []
         n, diff = 1, 0
         n_savings = s_savings = 0
         while n < max_iter and diff != 'pass':
             n_land += diff
             n_land_list.append(n_land) 
             spendings, responses = self.ResponseList(n_land, n, n_savings, s_savings, saving)
             eq_spending = self.FindNE(spendings, responses)
             if not saving:
                 n_savings += spendings[0][-1] - eq_spending[0]
                 s_savings += spendings[1][-1] - eq_spending[1] 
             else:
                 n_savings = spendings[0][-1] - eq_spending[0]
                 s_savings = spendings[1][-1] - eq_spending[1] 
             diff = self.IfEqSpending(n_land, eq_spending)
             ns_best_spending.append(eq_spending)
             spe_res.append([spendings, responses])
             n += 1
         if diff == 'pass' and verbose==True:
             print('Convergence succeeded in iteration: {}'.format(n))
             print('Land in Nash equilibrium for native and settler are: {:.2f} and {:.2f}'.format(n_land, 100-n_land))
             print('Spending in Nash equilibrium of native and settler are: {:.2f} and {:.2f}'.format(eq_spending[0], eq_spending[1]))
             print(f'Native saving = {n_savings:.2f}, Settler saving = {s_savings:.2f}')
         elif n == max_iter and verbose==True:
             print('Convergence failed!')
         return np.array(ns_best_spending), np.array(n_land_list), spe_res
     
    def PeriodResults(self, ns_spending, n_land, t=20):
         n_income = self.ie.NativeIncome(n_land)
         s_income = self.ie.SettlerIncome(100 - n_land)
         n_best_spending, s_best_spending = np.transpose(ns_spending)
         n_cons = n_income - n_best_spending
         s_cons = s_income - s_best_spending
         values = [n_land, n_best_spending, s_best_spending, n_cons, s_cons]
         titles = ["Native's land: ", "Native's spending: ", "Settler's spending: ", "Native's consumption: ", "Settler's consumption: "]
         for title, value in zip(titles, values):
             print(title)
             print(np.around(value[:t], 2)) if len(value) > t else print(np.around(value, 2))
             print()
         fig, (axes) = plt.subplots(1, 3, sharex = True, figsize = (14, 12))
         titles2 = ['Period spending', 'Period consumption', 'Cumulative consumptions']
         n_values = [n_best_spending, n_cons, np.cumsum(n_cons)]
         s_values = [s_best_spending, s_cons, np.cumsum(s_cons)]
         for ax, title, n_value, s_value in zip(axes, titles2, n_values, s_values):
             ax.plot(range(t), n_value[:t], label = 'Native')
             ax.plot(range(t), s_value[:t], label = 'Settler')
             ax.set(xlabel=title)
             ax.legend()
             ax.grid()
         plt.show()
    
    def SpendingShocks(self, n_savings, n_spendings, s_savings, s_spendings, shock_size):
        mu, sd = shock_size
        n_shock, s_shock = mu + sd*np.random.randn(2)
        n_final_spendings = n_spendings + n_shock
        s_final_spendings = s_spendings + s_shock
        if n_final_spendings > n_savings or n_final_spendings < 0:
            n_final_spendings = n_spendings
        if s_final_spendings > s_savings or s_final_spendings < 0:
            s_final_spendings = s_spendings
        return n_final_spendings, s_final_spendings
         
    def Simulation(self, n_land, un_periods, saving=True, shock=True, shock_size=(0, 2)): #[n_income_list, s_income_list], [s_best_spending, n_best_spending]
         '''
         Take the intial land of Native and uncertainty periods. Return total periods, native and settler's final profit.
         
         Parameters:
         ----------
             n_land (float): Native's land.
             un_periods (int): uncertainty periods.
             saving (bool): whether allow players saving.
             shock (bool): whether add shock to each period.
             shock_size (array-like[float,float]): support normal shock. The first param is mean and the second is sd.
         '''
         tot_periods = self.pd.n_dft + un_periods
         n, diff = 1, 0
         n_savings = s_savings = 0
         while n <= tot_periods:
             n_land += diff
             spendings, responses = self.ResponseList(n_land, n, n_savings, s_savings, saving)
             eq_spending = self.FindNE(spendings, responses)
             if shock:
                 eq_spending = self.SpendingShocks(spendings[0][-1], eq_spending[0], spendings[1][-1], eq_spending[1], shock_size)
             if not saving:
                 n_savings += spendings[0][-1] - eq_spending[0]
                 s_savings += spendings[1][-1] - eq_spending[1] 
             else:
                 n_savings = spendings[0][-1] - eq_spending[0]
                 s_savings = spendings[1][-1] - eq_spending[1] 
             diff = self.IfEqSpending(n_land, eq_spending, simulation=True)
             n += 1
         return tot_periods, round(n_savings, 2), round(s_savings, 2)
    


if __name__ == "__main__": 
    land = GraphPlot(0, 100, 1000)
    
    # two logistic functions A1, B1, C1, A2, B2, C2,     D, E, H, gamma_n, beta_s
    ie = IncomeExpansion(120, 0.045, 18, 180, 0.065, 40, 0, 100, 150, 0.5, 0.5) # both logistic income function
    #sum_income = [ie.NativeIncome(land.xvalues), ie.SettlerIncome(100 - land.xvalues), ie.NativeIncome(land.xvalues)+ie.SettlerIncome(100 - land.xvalues)]
    #sep_income = [pf.NativeIncome(land.xvalues), pf.SettlerIncome(land.xvalues)]
    #cost_profit = [players3.NativeMI(land.xvalues), players3.SettlerMI(land.xvalues), \
    #               players3.NativeExpanMC(land.xvalues), players3.SettlerExpanMC(land.xvalues)]
    #land.IncomeGraph(sum_income)
    #land.IncomeGraph(sep_income)
    #land.CostProfit(cost_profit)
    
    #time_start = time.time()
    pd = PlayerDecision(ie, 1/6, 10)
    dp = DP(ie, pd)
    #print(dp.Simulation(65, 5))
    ns_best_spending, n_land_list, spe_res = dp.DynamicNE(75, saving=False)
    dp.PeriodResults(ns_best_spending, n_land_list)
    #print(time.time() - time_start)
