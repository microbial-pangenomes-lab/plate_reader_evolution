#!/usr/bin/env python


import logging
import numpy as np
import pandas as pd

import seaborn as sns
from matplotlib import colors
import matplotlib.pyplot as plt
from matplotlib import rcParams

from .mic import hill_func


sns.set_style('ticks', rc={"axes.facecolor": (0, 0, 0, 0)})
sns.set_context('paper')

rcParams['font.family'] = 'sans-serif'

logger = logging.getLogger('evol.plot')


def create_figure(figsize=(5, 3)):
    return plt.figure(figsize=figsize, constrained_layout=True)


def make_color_dict(objects, cmap='hsv'):
    return {x: colors.rgb2hex(c)
            for x, c in zip(objects,
                            sns.color_palette(cmap, len(objects)))}


def plot_legend(o_colors, fname):
    plt.clf()
    sns.palplot(o_colors.values(), size=1)
    plt.xticks(range(len(o_colors)),
               labels=o_colors.keys(),
               rotation=90,
               size=16);
    plt.savefig(fname,
                dpi=300, bbox_inches='tight',
                transparent=True)
    plt.clf()


def plot_passages(df, t_colors, s_colors, fname,
                  title='OD600', cmap='viridis',
                  vmin=0, vmax=1):
    plt.clf()

    cm = sns.clustermap(data=df,
                        cmap=cmap,
                        vmin=vmin,
                        vmax=vmax,
                        row_cluster=False,
                        col_cluster=False,
                        row_colors=pd.DataFrame([[t_colors[x[0]],
                                                  s_colors[x[1]]]
                                                 for x in df.index],
                                                index=df.index,
                                                columns=['treatment-id', 'strain']),
                        cbar_pos=None,
                        figsize=(7, 12),
                        yticklabels=False)

    cm.ax_heatmap.set_ylabel('')
    #i = 0
    #for l in treatment:
    #    i += df.loc[l].shape[0]
    #    cm.ax_heatmap.axhline(i, lw=1.5, color='w')
    cm.ax_heatmap.set_title(title)

    plt.tight_layout(w_pad=0, h_pad=0)
    plt.savefig(fname,
                dpi=300, bbox_inches='tight',
                transparent=True)
    plt.clf()


def plot_appearance(df, s_colors, fname):
    plt.clf()

    cp = sns.catplot(data=df,
                     x='passage',
                     y='strain',
                     col='treatment-id',
                     col_wrap=2,
                     dodge=True,
                     s=8, alpha=0.6,
                     palette=s_colors.values(),
                     height=7, aspect=0.5)

    (cp.set_axis_labels('passage of first resistance', '',
                        size=16)
       .set_titles('{col_name}',
                   size=18)
     )

    for ax in cp.axes.flat:
        ax.axvline(df['passage'].max() - 0.5,
                   color='r',
                   ls='dashed')
        #ax.set_xticks(list(range(1, df['passage'].max() + 1, 2)))
        #ax.set_xticklabels(list(range(1, df['passage'].max(), 2)) + ['no']);
    
    plt.tight_layout(w_pad=0, h_pad=0)
    plt.savefig(fname,
                dpi=300, bbox_inches='tight',
                transparent=True)
    plt.clf()


def plot_plate(df, fname, fig=None, name=''):
    if fig is None:
        fig = create_figure()
    else:
        plt.clf()

    sns.heatmap(df.pivot_table(index='row',
                               columns='column',
                               values='od600').reindex(index=[x
                                                  for x in 'ABCDEFGH'],
                                                  columns=range(1, 13)),
                cmap='viridis',
                vmin=0,
                vmax=1,
                cbar=True)

    plt.ylabel('row')
    plt.xlabel('column')

    plt.title(name)
    plt.savefig(fname,
                dpi=300, bbox_inches='tight',
                transparent=True)
    plt.clf()


def plot_mic(df, params, fname, normalise=None, fig=None, name=''):
    if fig is None:
        fig = create_figure()
    else:
        plt.clf()

    plt.plot(df['concentration'],
             df['od600'],
             'ko',
             label='data')
    if normalise is not None:
        y = df['od600']
        ymin = y[y <= normalise]
        if y.max() > 0.5:
            ymax = np.mean(y[y > 0.5])
        else:
            ymax = y.max()
        if ymin.shape[0] != 0:
            ymin = np.median(ymin)
            y1 = (y - ymin) / (y.max() - ymin)
            y2 = (y - ymin) / (ymax - ymin)
            plt.plot(df['concentration'],
                    y1,
                    'b.',
                    label='normalised data')
            plt.plot(df['concentration'],
                    y2,
                    'g.',
                    label='normalised data (cMIC)')
    a, b, c, d, mic, cmic = params
    if not np.isnan(a):
        x = np.linspace(df[df['concentration'] != 0]['concentration'].min(),
                        df[df['concentration'] != 0]['concentration'].max(),
                        100)
        plt.plot(x,
                 hill_func(x, a, b, c, d),
                 '-',
                 color=sns.xkcd_rgb['dark grey'],
                 label='Hill fit')
        plt.plot(c,
                 hill_func(c, a, b, c, d),
                 'ro',
                 markersize=10,
                 label='IC50')
    
    if not np.isnan(mic):
        plt.axvline(mic,
                    color='r',
                    ls='dashed',
                    label='MIC')

    if not np.isnan(cmic):
        plt.axvline(cmic,
                color='xkcd:dark red',
                    ls='dashed',
                    label='cMIC')

    plt.legend(loc='best', facecolor='w', prop={'size': 6})

    plt.title(name)
    plt.ylim(-0.05, 1.05)
    plt.xlim(df[df['concentration'] != 0]['concentration'].min() -
             df[df['concentration'] != 0]['concentration'].min() / 4,
             df[df['concentration'] != 0]['concentration'].max() +
             df[df['concentration'] != 0]['concentration'].max() / 4)
    plt.xlabel('concentration')
    plt.ylabel('od600')
    plt.xscale('log')

    plt.savefig(fname,
                dpi=300, bbox_inches='tight',
                transparent=True)
    plt.clf()


def plot_growth_rate(df, params, fname, fig=None, name=''):
    if fig is None:
        fig = create_figure()
    else:
        plt.clf()

    plt.plot(df['time'],
             df['od600'],
             'k.')

    plt.ylabel('od600')
    plt.xlabel('time\n(hours)')

    plt.title(name)

    plt.twinx()
   
    plt.plot(params['time'],
             params['grate'],
             'r.')

    plt.ylabel('growth rate', color='r')
    plt.yticks(color='r');

    plt.axvline(params.sort_values('grate').iloc[-1]['time'],
                zorder=-1,
                ls='dashed', color='xkcd:grey')

    plt.savefig(fname,
                dpi=300, bbox_inches='tight',
                transparent=True)
    plt.clf()


