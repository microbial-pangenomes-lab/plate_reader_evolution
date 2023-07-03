# Copyright 2019 Marco Galardini

import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit


logger = logging.getLogger('evol.mic')


def compute_mic(values, threshold=0.3, normalise=None):
    """Compute MIC

    Args:
        values (pandas.Series)
            MIC curve data, must contain `concentration`, `od600`
            and `strain` columns
        threshold (float)
            OD values above the threshold
            are considered growth
        normalise (float or None)
            Whether to normalise the data (i.e. bringing it to a 0-1 range).
            The provided value is used to compute the minimum values to have
            a more robust normalization (the mean of od600 below this
            value is used)

    Returns:
        mic (float)
            MIC estimate
    """
    y = values['od600']
    v = None
    if normalise is not None:
        # robust normalisation
        # use an average of all OD values
        # below a sensible OD threshold
        ymin = y[y <= normalise]
        # also remove artifacts from very high
        # OD values
        if y.max() > 0.5:
            ymax = np.mean(y[y > 0.5])
        else:
            ymax = y.max()
        if ymin.shape[0] == 0:
            v = values['concentration'].max()
        else:
            ymin = np.mean(ymin)
            y = (y - ymin) / (ymax - ymin)
    values['normalized'] = y
    if v is None:
        # tentative MIC value
        v = values[y < threshold]['concentration']
        if v.shape[0] == 0:
            v = values['concentration'].max()
        else:
            v = v.min()
    # check that there are no values above threshold with higher conc.
    w = values[y >= threshold]['concentration'].max()
    if w > v:
        # tolerate up to 1
        # wells below the threshold to call the cMIC
        values = values.sort_values('concentration')
        if values[(values['concentration'] < w) &
                  (values['normalized'] < threshold)].groupby('concentration').count().shape[0] < 2:
            v = values[(values['concentration'] > w) &
                       (values['normalized'] < threshold)]['concentration'].min()
        else:
            v = np.nan
        return v
    return v


def hill_func(x, a, b, c, d):
    """Hill function
    commonly used to fit MIC curves

    Args:
        x (numpy.array)
            Concentration vector (n, 1)
        a (float)
        b (float)
        c (float)
        d (float)

    Returns:
        y (float)
    """
    return a+(b-a)/(1+(x/c)**d)


def fit_hill(v, estimate=True, sanity=None, normalise=None, maxfev=999999):
    """Fit the Hill function to a MIC curve

    Args:
        v (pandas.DataFrame)
            MIC curve data, must contain `concentration` and `od600` columns
        estimate (bool)
            Whether to estimate the initial values for the parameters
        sanity (float or None)
            Whether to check if the data is an actual Hill curve,
            if the delta between highest and lowest OD is below
            this value, do not fit the curve.
            Additionally, if the Spearman correlation between OD and 
            [treatment] is above 0.2 or the maximum OD is above 0.2,
            the curve is also not fitted.
        normalise (float or None)
            Whether to normalise the data (i.e. bringing it to a 0-1 range).
            The provided value is used to compute the minimum values to have
            a more robust normalization (the mean of od600 below this
            value is used)
        maxfev (int)
            Maximum iterations for curve fitting

    Returns:
        out (pd.Series)
            Fitted curve parameters and standard deviations
    """
    index = ['a', 'b', 'c', 'd',
             'SDa', 'SDb',
             'SDc', 'SDd']
    v = v[v['concentration'] != 0]
    x = v['concentration'].values
    y = v['od600'].values
    if normalise is not None:
        # robust normalisation
        # use an average of all OD values
        # below a sensible OD threshold
        ymin = y[y <= normalise]
        if ymin.shape[0] == 0:
            c = v['concentration'].max()
            return pd.Series([np.nan, np.nan, c, np.nan,
                              np.nan, np.nan, np.nan, np.nan],
                             index=index)
        ymin = np.mean(ymin)
        y = (y - ymin) / (y.max() - ymin)
    if estimate:
        p0 = [y.min(),
              y.max(),
              x.mean(),
              1.0]
    else:
        p0 = None
    if sanity is not None:
        discard = False
        if abs(y.max() - y.min()) <= sanity:
            discard = True
        if stats.spearmanr(x, y)[0] > 0.2:
            discard = True
        if y.max() < 0.2:
            discard = True
        if discard:
            if y.mean() < 0.1:
                c = x.min()
            else:
                c = x.max()
            return pd.Series([np.nan, np.nan, c, np.nan,
                              np.nan, np.nan, np.nan, np.nan],
                             index=index)
    try:
        params = curve_fit(hill_func,
                           x, y,
                           p0=p0,
                           maxfev=maxfev)
        [a, b, c, d] = params[0]
        pcov = params[1]
        [sda, sdb, sdc, sdd] = np.sqrt(np.diag(pcov))
        if c > x.max():
            return pd.Series([np.nan, np.nan, x.max(), np.nan,
                              np.nan, np.nan, np.nan, np.nan],
                             index=index)
        return pd.Series([a, b, c, d, sda, sdb, sdc, sdd],
                         index=index)
    except RuntimeError as e:
        logger.warning(str(e))
        return pd.Series([np.nan, np.nan, np.nan, np.nan,
                          np.nan, np.nan, np.nan, np.nan],
                         index=index)


def mod_gompertz(x, A, B, C, M):
    """Modified Gompertz function
    Commonly used to fit MIC curves
    ref: doi:10.1046/j.1365-2672.2000.01017.x
    thanks to Emma Briars for the tip

    Args:
        x (numpy.array)
            Concentration vector in log10 (n, 1)
        A (float)
        B (float)
        C (float)
        M (float)

    Returns:
        y (float)
    """
    return A + C * np.exp(-np.exp(B * (x - M)))


def fit_gompertz(v, estimate=True, sanity=None, normalise=None, maxfev=999999):
    """Fit the Gompertz function to a MIC curve

    Args:
        v (pandas.DataFrame)
            MIC curve data, must contain `concentration` and `od600` columns
        estimate (bool)
            Whether to estimate the initial values for the parameters
        sanity (float or None)
            Whether to check if the data is an actual Hill curve,
            if the delta between highest and lowest OD is below
            this value, do not fit the curve.
            Additionally, if the Spearman correlation between OD and 
            [treatment] is above 0.2 or the maximum OD is above 0.2,
            the curve is also not fitted. 
        normalise (float or None)
            Whether to normalise the data (i.e. bringing it to a 0-1 range).
            The provided value is used to compute the minimum values to have
            a more robust normalization (the mean of od600 below this
            value is used)
        maxfev (int)
            Maximum iterations for curve fitting

    Returns:
        out (pd.Series)
            Fitted curve parameters and standard deviations
    """
    index = ['a', 'b', 'c', 'd',
             'SDa', 'SDb',
             'SDc', 'SDd', 'mic']
    v = v[v['concentration'] != 0]
    x = np.log10(v['concentration'].values)
    y = v['od600'].values
    if normalise is not None:
        # robust normalisation
        # use an average of all OD values
        # below a sensible OD threshold
        ymin = y[y <= normalise]
        if ymin.shape[0] == 0:
            mic = v['concentration'].max()
            return pd.Series([np.nan, np.nan, np.nan, np.nan,
                              np.nan, np.nan, np.nan, np.nan,
                              mic],
                             index=index)
        ymin = np.mean(ymin)
        y = (y - ymin) / (y.max() - ymin)
    if estimate:
        p0 = [y.min() / 10,
              0.8,
              1,
              x.max() / 2]
    else:
        p0 = None
    if sanity is not None:
        discard = False
        yab = v['od600']
        if abs(yab.max() - yab.min()) <= sanity:
            discard = True
        if stats.spearmanr(x, y)[0] > 0.2:
            discard = True
        if y.max() < 0.2:
            discard = True
        if discard:
            if y.mean() < 0.1:
                mic = v[v['concentration'] != 0]['concentration'].min()
            else:
                mic = v['concentration'].max()
            return pd.Series([np.nan, np.nan, np.nan, np.nan,
                              np.nan, np.nan, np.nan, np.nan,
                              mic],
                             index=index)
    try:
        params = curve_fit(mod_gompertz,
                           x, y,
                           p0=p0,
                           maxfev=maxfev)
        [a, b, c, d] = params[0]
        mic = 10**(d + 1/b)
        pcov = params[1]
        [sda, sdb, sdc, sdd] = np.sqrt(np.diag(pcov))
        if mic > v['concentration'].max():
            return pd.Series([np.nan, np.nan, np.nan, np.nan,
                              np.nan, np.nan, np.nan, np.nan,
                              v['concentration'].max()],
                             index=index)
        if mic < v['concentration'].min():
            return pd.Series([np.nan, np.nan, np.nan, np.nan,
                              np.nan, np.nan, np.nan, np.nan,
                              v[v['concentration'] != 0]['concentration'].min()],
                             index=index)
        return pd.Series([a, b, c, d, sda, sdb, sdc, sdd, mic],
                         index=index)
    except RuntimeError as e:
        logger.warning(str(e))
        return pd.Series([np.nan, np.nan, np.nan, np.nan,
                          np.nan, np.nan, np.nan, np.nan,
                          np.nan],
                         index=index)
