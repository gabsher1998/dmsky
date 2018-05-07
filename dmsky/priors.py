# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Classes to manage priors
"""
from __future__ import absolute_import, division, print_function

import numpy as np
import scipy.stats as stats
from scipy.interpolate import interp1d

from dmsky.utils import stat_funcs
from dmsky.utils import tools

class PriorFunctor(object):
    """A functor class that wraps simple functions we use to
       make priors on parameters.
    """

    def __init__(self, funcname):
        self._funcname = funcname

    def normalization(self):
        """Normalization, i.e. the integral of the function
           over the normalization_range.
        """
        return 1.

    def normalization_range(self):
        """Normalization range.
        """
        return 0, np.inf

    def mean(self):
        """Mean value of the function.
        """
        return 1.

    def sigma(self):
        """The 'width' of the function.
        What this means depend on the function being used.
        """
        raise NotImplementedError(
            "prior_functor.sigma must be implemented by sub-class")

    @property
    def funcname(self):
        """A string identifying the function.
        """
        return self._funcname

    def marginalization_bins(self):
        """Binning to use to do the marginalization integrals
        """
        log_mean = np.log10(self.mean())
        # Default is to marginalize over two decades,
        # centered on mean, using 1000 bins
        return np.logspace(-1. + log_mean, 1. + log_mean, 1001)

    def profile_bins(self):
        """ The binning to use to do the profile fitting
        """
        log_mean = np.log10(self.mean())
        log_half_width = max(5. * self.sigma(), 3.)
        # Default is to profile over +-5 sigma,
        # centered on mean, using 100 bins
        return np.logspace(log_mean - log_half_width,
                           log_mean + log_half_width, 101)

    def log_value(self, x):
        """
        """
        return np.log(self.__call__(x))


class FunctionPrior(PriorFunctor):
    """
    """

    def __init__(self, funcname, mu, sigma, fn, lnfn=None):
        """
        """
        # FIXME, why doesn't super(function_prior,self) work here?
        PriorFunctor.__init__(self, funcname)
        self._mu = mu
        self._sigma = sigma
        self._fn = fn
        self._lnfn = lnfn

    def normalization(self):
        """ The normalization 
        i.e., the intergral of the function over the normalization_range 
        """
        norm_r = self.normalization_range()
        return quad(self, norm_r[0], norm_r[1])[0]

    def mean(self):
        """ The mean value of the function.
        """
        return self._mu

    def sigma(self):
        """ The 'width' of the function.
        What this means depend on the function being used.
        """
        return self._sigma

    def log_value(self, x):
        """
        """
        if self._lnfn is None:
            return np.log(self._fn(x, self._mu, self._sigma))
        return self._lnfn(x, self._mu, self._sigma)

    def __call__(self, x):
        """ Normal function from scipy """
        return self._fn(x, self._mu, self._sigma)


class GaussPrior(FunctionPrior):
    """
    """
    def __init__(self, mu, sigma):
        """
        """
        super(GaussPrior, self).__init__("gauss", mu, sigma, fn=stat_funcs.gauss, lnfn=stat_funcs.lngauss)
  
class LGaussPrior(FunctionPrior):
    """
    """
    def __init__(self, mu, sigma):
        """
        """
        super(LGaussPrior, self).__init__("lgauss", mu, sigma, fn=stat_funcs.lgauss, lnfn=stat_funcs.lnlgauss)
  
class LGaussLikePrior(FunctionPrior):
    """
    """
    def __init__(self, mu, sigma):
        """
        """
        def fn(x, y, s): return stat_funcs.lgauss(y, x, s)        
        def lnfn(x, y, s): return stat_funcs.lnlgauss(y, x, s)
        super(LGaussLikePrior, self).__init__("lgauss_like", mu, sigma, fn=fn, lnfn=lnfn)
 
class LGaussLogPrior(FunctionPrior):
    """
    """
    def __init__(self, mu, sigma):
        """
        """
        def fn(x, y, s): return stat_funcs.lgauss(x, y, s, logpdf=True)
        def lnfn(x, y, s): return stat_funcs.lnlgauss(x, y, s, logpdf=True)
        super(LGaussLogPrior, self).__init__("lgauss_log", mu, sigma, fn=fn, lnfn=lnfn)
  

class LognormPrior(PriorFunctor):
    """ A wrapper around the lognormal function.

    A note on the highly confusing scipy.stats.lognorm function...
    The three inputs to this function are:
    s           : This is the variance of the underlying 
                  gaussian distribution
    scale = 1.0 : This is the mean of the linear-space 
                  lognormal distribution.
                  The mean of the underlying normal distribution
                  occurs at ln(scale)
    loc = 0     : This linearly shifts the distribution in x (DO NOT USE)

    The convention is different for numpy.random.lognormal
    mean        : This is the mean of the underlying 
                  normal distribution (so mean = log(scale))
    sigma       : This is the standard deviation of the 
                  underlying normal distribution (so sigma = s)

    For random sampling:
    numpy.random.lognormal(mean, sigma, size)
    mean        : This is the mean of the underlying 
                  normal distribution (so mean = exp(scale))
    sigma       : This is the standard deviation of the 
                  underlying normal distribution (so sigma = s)

    scipy.stats.lognorm.rvs(s, scale, loc, size)
    s           : This is the standard deviation of the 
                  underlying normal distribution
    scale       : This is the mean of the generated 
                  random sample scale = exp(mean)

    Remember, pdf in log space is
    plot( log(x), stats.lognorm(sigma,scale=exp(mean)).pdf(x)*x )

    Parameters
    ----------
    mu : float
        Mean value of the function
    sigma : float
        Variance of the underlying gaussian distribution
    """

    def __init__(self, mu, sigma):
        super(LognormPrior, self).__init__('lognorm')
        self._mu = mu
        self._sigma = sigma

    def mean(self):
        """Mean value of the function.
        """
        return self._mu

    def sigma(self):
        """ The 'width' of the function.
        What this means depend on the function being used.
        """
        return self._sigma

    def __call__(self, x):
        """ Log-normal function from scipy """
        return stats.lognorm(self._sigma, scale=self._mu).pdf(x)


class NormPrior(PriorFunctor):
    """ A wrapper around the normal function.
    Parameters
    ----------
    mu : float
        Mean value of the function
    sigma : float
        Variance of the underlying gaussian distribution
    """

    def __init__(self, mu, sigma):
        """
        """
        super(NormPrior, self).__init__('norm')
        self._mu = mu
        self._sigma = sigma

    def mean(self):
        """Mean value of the function.
        """
        return self._mu

    def sigma(self):
        """ The 'width' of the function.
        What this means depend on the function being used.
        """
        return self._sigma

    def __call__(self, x):
        """Normal function from scipy """
        return stats.norm(loc=self._mu, scale=self._sigma).pdf(x)


class FileFuncPrior(PriorFunctor):
    """ A wrapper around the interpolated function.
    Parameters
    ----------
    filename : string
        File with the function parameters
    """

    def __init__(self, filename):
        """
        """
        super(FileFuncPrior, self).__init__('file')
        self._filename = filename
        d = tools.yaml_load(self._filename)
        self._mu = d['mean']
        self._sigma = d['sigma']
        self._x = d['x']
        self._y = d['y']
        self._kind = d.get('kind', 'linear')
        self._fill_value = d.get('fill_value', 0)
        self._interpfunc = interp1d(self._x, self._y, kind=self._kind,
                                    bounds_error=False, fill_value=self._fill_value)

    def mean(self):
        """Mean value of the function.
        """
        return self._mu

    def sigma(self):
        """ The 'width' of the function.
        What this means depend on the function being used.
        """
        return self._sigma

    def __call__(self, x):
        """Normal function from scipy """
        return self._interpfunc(x)


def create_prior_functor(d):
    """Build a prior from a dictionary.

    Parameters
    ----------
    d     :  A dictionary, it must contain:
       d['functype'] : a recognized function type
                       and all of the required parameters for the 
                       prior_functor of the desired type

    Returns
    ----------
    A sub-class of '~fermipy.stats_utils.prior_functor'

    Recognized types are:

    'lognorm'       : Scipy lognormal distribution
    'norm'          : Scipy normal distribution
    'gauss'         : Gaussian truncated at zero
    'lgauss'        : Gaussian in log-space
    'lgauss_like'   : Gaussian in log-space, with arguments reversed. 
    'lgauss_logpdf' : ???
    """
    functype = d.pop('functype', 'lgauss_like')
    if functype == 'norm':
        return NormPrior(**d)
    elif functype == 'lognorm':
        return LognormPrior(**d)
    elif functype == 'gauss':
        return FunctionPrior(functype, d['mu'], d['sigma'], stat_funcs.gauss, stat_funcs.lngauss)
    elif functype == 'lgauss':
        return FunctionPrior(functype, d['mu'], d['sigma'], stat_funcs.lgauss, stat_funcs.lnlgauss)
    elif functype in ['lgauss_like', 'lgauss_lik']:
        def fn(x, y, s): return stat_funcs.lgauss(y, x, s)

        def lnfn(x, y, s): return stat_funcs.lnlgauss(y, x, s)
        return FunctionPrior(functype, d['mu'], d['sigma'], fn, lnfn)
    elif functype == 'lgauss_log':
        def fn(x, y, s): return stat_funcs.lgauss(x, y, s, logpdf=True)

        def lnfn(x, y, s): return stat_funcs.lnlgauss(x, y, s, logpdf=True)
        return FunctionPrior(functype, d['mu'], d['sigma'], fn, lnfn)
    elif functype == 'interp':
        return FileFuncPrior(d['filename'])
    else:
        raise KeyError("Unrecognized prior_functor type %s" % functype)


def factory(ptype, **kwargs):
    import dmsky.factory

    prior_copy = kwargs.copy()            
    return dmsky.factory.factory(ptype, module=__name__,**prior_copy)
