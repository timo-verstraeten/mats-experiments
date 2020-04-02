import scipy as sp
import scipy.stats

class Posterior():

    @property
    def mean(self):
        raise NotImplementedError()

    def update(self, x):
        raise NotImplementedError()


class BetaPosterior(Posterior):
    
    def __init__(self, alpha=0.5, beta=0.5):
        self.a = alpha
        self.b = beta

    @property
    def mean(self):
        return self.a / (self.a + self.b)
    
    def update(self, x):
        self.a += x
        self.b += 1 - x
    
    def sample(self):
        return sp.stats.beta(a=self.a, b=self.b).rvs(1)[0]


################

class GaussianPosterior(Posterior):

    def __init__(self, std, type='jeffreys'):
        self._std = std
        self._type = type
        self._count = 0

        # Check whether prior type exists
        if type == 'jeffreys':
            # Improper mean
            self._mu = None
        else:
            raise ValueError('This prior type does not exist')
                
    @property
    def mean(self):
        return self._mu

    @property
    def _sigma(self):
        return self._std / self._count

    def update(self, x):
        self._mu = x if self._mu is None else (self._mu + x)
        self._count += 1

    def sample(self):
        if self._count == 0:
            #TODO: this should by decided within the TS sampler
            return sp.stats.uniform(loc=0, scale=1).rvs(1)[0]
            #TODO return None
        else:
            return sp.stats.norm(loc=self._mu, scale=self._sigma).rvs(1)[0]
