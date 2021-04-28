import numpy as np
from scipy.optimize import fsolve
from scipy.optimize import newton_krylov
from scipy.optimize import least_squares, minimize

class IncomeExpansion():
    def __init__(self, A1, B1, C1, A2, B2, C2, D, E, H, gamma, beta, prob):
        self.A1, self.B1, self.C1 = A1, B1, C1
        self.D, self.E, self.H, self.gamma, self.beta = D, E, H, gamma, beta
        self.A2, self.B2, self.C2 = A2, B2, C2
        self.periods = (1 - prob)/prob
    def NativeIncome(self, land):
        A1, B1, C1 = self.A1, self.B1, self.C1
        return  A1/(1+ np.exp(-B1* (land - C1)) - A1/(1+ np.exp(B1 * C1)))
    def NativeMI(self, land):
        A1, B1, C1 = self.A1, self.B1, self.C1
        ex = np.exp(-B1*(land - C1))
        return B1 * A1 * ex/(1+ ex)**2 
    def SettlerIncome(self, land):
        A2, B2, C2 = self.A2, self.B2, self.C2 
        return A2/(1+ np.exp(-B2* (land - C2)) - A2/(1+ np.exp(B2 * C2))) 
    def SettlerMI(self, land):
        A2, B2, C2 = self.A2, self.B2, self.C2
        ex = np.exp(-B2*(land - C2))
        return B2 * A2 * ex/(1+ ex)**2 
    def NativeExpan(self, spending, land):
        D, H, gamma = self.D, self.H, self.gamma
        return  spending**(1 - gamma)/(land + D) * (H - land)
    def NativeExpanMG(self, spending, land):
        D, H, gamma = self.D, self.H, self.gamma
        return  spending**(-gamma)/(land + D) * (H - land) * (1 - gamma)
    def SettlerExpan(self, spending, land):
        D, E, H, beta = self.D, self.E, self.H, self.beta
        return  spending**(1 - beta)/(land + D + E) * (H - land)
    def SettlerExpanMG(self, spending, land):
        D, E, H, beta = self.D, self.E, self.H, self.beta
        return  spending**(-beta)/(land + D + E) * (H - land) * (1 - beta)
    def NativeFOC(self, land, n_spending, s_spending):
        n_gain = self.NativeExpan(n_spending, land) - self.SettlerExpan(s_spending, 100 - land)
        n_foc = self.NativeMI(land + n_gain) * self.NativeExpanMG(n_spending, land) * self.periods - 1
        return n_foc
    def SettlerFOC(self, land, n_spending, s_spending):
        s_gain = - self.NativeExpan(n_spending, 100 - land) + self.SettlerExpan(s_spending, land)
        s_foc = self.SettlerMI(land + s_gain) * self.SettlerExpanMG(s_spending, land) * self.periods - 1
        return s_foc
    def ComFuns(self, inits):
        land, n_spending, s_spending = inits
        return np.array([self.NativeFOC(land, n_spending, s_spending), 
                         self.SettlerFOC(100 - land, n_spending, s_spending), 
                         self.NativeExpan(n_spending, land) - self.SettlerExpan(s_spending, 100-land)])

def find_eq(params, if_eq = False):
    D, E, H, alpha = params
    ##################### A1,  B1,  C1,  A2,  B2,    C2, D,   E, H,  gamma, beta, prob
    ie = IncomeExpansion(120, 0.045, 18, 180, 0.065, 40, D, E, H, alpha, alpha, 1/6)
    z = least_squares(ie.ComFuns, np.array([40, 20, 40]), bounds=([0, 0.1, 0.1], [100, 200, 200]))
    if if_eq :
        return z.x
    else:
        return (z.x[0] - 60)**2

x0 = np.array([5, 20, 120, 0.4])
bounds = np.array([[0, 100], [10, 100], [100, 150], [0.1, 0.5]])
res = minimize(find_eq, x0=x0, method="L-BFGS-B", bounds=bounds)
print(res.x, res.success, res.fun)
eq_res = find_eq(np.array(res.x), True)
print("The resulting eq. is: ",  eq_res)
