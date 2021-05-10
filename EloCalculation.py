import math

class EloCalculation:
    def __init__(self, eloA, eloB, playedA, playedB):
        self.eloA = eloA
        self.eloB = eloB
        self.K = 30
        self.Pb = self.prob(eloA, eloB)
        self.Pa = self.prob(eloB, eloA)
        if playedA < 1:
            self.multA = 1.5
        else:
            self.multA = 1

        if playedB < 1:
            self.multB = 1.5
        else:
            self.multB = 1

    @staticmethod
    def prob(a, b):
        return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (a - b) / 400))

    def calculate(self, d):
        if d == 1:
            Ra = self.eloA + (self.K * (1 - self.Pa))*self.multA
            Rb = self.eloB + (self.K * (0 - self.Pb))*self.multB
        else:
            Ra = self.eloA + (self.K * (0 - self.Pa))*self.multA
            Rb = self.eloB + (self.K * (1 - self.Pb))*self.multB
        if Ra < 0:
            Ra = 0
        if Rb < 0:
            Rb = 0
        return round(Ra), round(Rb)