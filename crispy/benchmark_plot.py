#!/usr/bin/env python
# Copyright (C) 2017 Emanuel Goncalves

import numpy as np
import pandas as pd
import seaborn as sns
import scipy.stats as st
import matplotlib.pyplot as plt
from sklearn.metrics.ranking import auc


def plot_cumsum_auc(X, index_set, ax=None, cmap='viridis', legend=True):
    """
    Plot cumulative sum of values X considering index_set list.

    :param DataFrame X: measurements values
    :param Series index_set: list of indexes in X
    :param String ax: matplotlib Axes
    :param String cmap: Matplotlib color map
    :param Bool legend: Plot legend

    :return matplotlib Axes, plot_stats dict:
    """

    if ax is None:
        ax = plt.gca()

    plot_stats = {
        'auc': {}
    }

    for c, f in zip(sns.color_palette(cmap, X.shape[1]).as_hex(), list(X)):
        # Build data-frame
        x = X[f].sort_values().dropna()

        # Observed cumsum
        y = x.index.isin(index_set)
        y = np.cumsum(y) / sum(y)

        # Rank fold-changes
        x = st.rankdata(x) / x.shape[0]

        # Calculate AUC
        f_auc = auc(x, y)
        plot_stats['auc'][f] = f_auc

        # Plot
        ax.plot(x, y, label='%s: %.2f' % (f, f_auc), lw=1., c=c)

        # Random
        ax.plot((0, 1), (0, 1), 'k--', lw=.3, alpha=.5)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.set_xlabel('Ranked')
    ax.set_ylabel('Cumulative sum %s' % index_set.name)

    if legend:
        ax.legend(loc=4)

    return ax, plot_stats


def plot_cnv_rank(x, y, ax=None, stripplot=True):
    """
    Plot copy-number versus ranked y values.

    :param String x:
    :param String y:
    :param Matplotlib Axes ax:
    :param Boolean stripplot:

    :return Matplotlib Axes ax, plot_stats dict:
    """

    if ax is None:
        ax = plt.gca()

    plot_stats = {}

    boxplot_args = {'linewidth': .3, 'notch': True, 'fliersize': 1, 'orient': 'v', 'palette': 'viridis', 'sym': '' if stripplot else '.'}
    stripplot_args = {'orient': 'v', 'palette': 'viridis', 'size': 0.5, 'linewidth': .05, 'edgecolor': 'white', 'jitter': .15, 'alpha': .75}

    y_ranked = pd.Series(st.rankdata(y) / y.shape[0], index=y.index).loc[x.index]

    sns.boxplot(x, y_ranked, ax=ax, **boxplot_args)

    if stripplot:
        sns.stripplot(x, y_ranked, ax=ax, **stripplot_args)

    ax.axhline(.5, lw=.1, c='black', alpha=.5)

    ax.set_xlabel('Copy-number (absolute)')
    ax.set_ylabel('Ranked %s' % y.name)

    return ax, plot_stats


def plot_chromosome(pos, original, mean, se=None, ax=None):
    # TODO: add extra plotting variables

    if ax is None:
        ax = plt.gca()

    # Plot original values
    ax.scatter(pos, original, s=2, marker='.', lw=0, c='#b1b1b1', alpha=.5)

    # Plot corrected values
    ax.scatter(pos, mean, s=4, marker='.', lw=0, c='#F2C500', alpha=.9)

    if se is not None:
        ax.fill_between(pos, mean - se, mean + se, c='#F2C500', alpha=0.2)

    # Misc
    ax.axhline(0, lw=.3, ls='-', color='black')

    # Labels and dim
    ax.set_ylabel('CHRM %s' % pos.name)
    ax.set_xlim(0, pos.max())
