# Copyright 2019 Marco Galardini

import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit


logger = logging.getLogger('evol.mic')


def compute_mic(values, tolerance=0.15):
    """Compute MIC

    Args:
        values (pandas.DataFrame)
            MIC curve data, must contain `concentration`, `od600`
            and `strain` columns
        tolerance (float)
            OD values above the plate minumum plus tolerance
            are considered growth

    Returns:
        mic (pandas.DataFrame)
    """
    min_od = values['od600'].min()
    v = values[(values['od600'] < min_od + tolerance)
                 ].groupby(['strain'])['concentration'].min()
    v = v.reindex(values['strain'].unique())
    v[np.isnan(v)] = values['concentration'].max()
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


def fit_hill(v, estimate=True, sanity=None, normalise=False, maxfev=999999):
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
        normalise (bool)
            Whether to normalise the data (i.e. bringing it to a 0-1 range)
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
    if estimate:
        p0 = [v['od600'].min(),
              v['od600'].max(),
              v['concentration'].mean(),
              1.0]
    else:
        p0 = None
    x = v['concentration'].values
    y = v['od600'].values
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
    if normalise:
        y = y / np.linalg.norm(y)
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


def fit_gompertz(v, estimate=True, sanity=None, normalise=False, maxfev=999999):
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
        normalise (bool)
            Whether to normalise the data (i.e. bringing it to a 0-1 range)
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
    if estimate:
        p0 = [v['od600'].min() / 10,
              0.8,
              1,
              np.log10(v['concentration'].max() / 2)]
    else:
        p0 = None
    x = np.log10(v['concentration'].values)
    y = v['od600'].values
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
    if normalise:
        y = y / np.linalg.norm(y)
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
