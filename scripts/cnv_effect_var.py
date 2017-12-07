#!/usr/bin/env python
# Copyright (C) 2017 Emanuel Goncalves

import os
import crispy
import pickle
import numpy as np
import pandas as pd
import seaborn as sns
import scipy.stats as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import mode
from crispy import bipal_dbgd
from natsort import natsorted
from sklearn.metrics import roc_auc_score
from crispy.benchmark_plot import plot_cnv_rank
from sklearn.linear_model import LinearRegression


# - Imports
# Ploidy
ploidy = pd.read_csv('data/gdsc/cell_lines_project_ploidy.csv', index_col=0)['Average Ploidy']

# sgRNA library
sgrna_lib = pd.read_csv('data/gdsc/crispr/KY_Library_v1.1_annotated.csv', index_col=0).dropna(subset=['STARTpos', 'GENES'])

# Non-expressed genes
nexp = pickle.load(open('data/gdsc/nexp_pickle.pickle', 'rb'))

# GDSC
fc = pd.read_csv('data/crispr_gdsc_logfc.csv', index_col=0)
ccrispy = pd.read_csv('data/crispr_gdsc_crispy.csv', index_col=0)
c_gdsc = pd.DataFrame({
    os.path.splitext(f)[0].replace('crispr_gdsc_crispy_', ''):
        pd.read_csv('data/crispy/' + f, index_col=0)['k_mean']
    for f in os.listdir('data/crispy/') if f.startswith('crispr_gdsc_crispy_')
}).dropna()

# Copy-number absolute counts
cnv = pd.read_csv('data/gdsc/copynumber/Gene_level_CN.txt', sep='\t', index_col=0)
cnv = cnv.loc[:, cnv.columns.isin(list(c_gdsc))]
cnv_abs = cnv.drop(['chr', 'start', 'stop'], axis=1).applymap(lambda v: int(v.split(',')[1]))

# Copy-number segments
cnv_seg = pd.read_csv('data/gdsc/copynumber/Summary_segmentation_data_994_lines_picnic.txt', sep='\t')
cnv_seg['chr'] = cnv_seg['chr'].replace(23, 'X').replace(24, 'Y').astype(str)
cnv_seg = cnv_seg[cnv_seg['cellLine'].isin(set(c_gdsc))]

cnv_seg_c = []
for s in set(cnv_seg['cellLine']):
    for c in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22']:
        seg = cnv_seg[(cnv_seg['cellLine'] == s) & (cnv_seg['chr'] == c)]
        seg_c = [((e - s) * (c + 1), (e - s)) for i, (s, e, c) in enumerate(seg[['startpos', 'endpos', 'totalCN']].values)]
        d, n = zip(*(seg_c))
        cpv = sum(d) / sum(n) - 1
        cnv_seg_c.append({'sample': s, 'chr': c, 'ploidy': cpv})
cnv_seg_c = pd.DataFrame(cnv_seg_c)
cnv_seg_c = cnv_seg_c.groupby(['sample', 'chr']).first()


# - Overlap
genes, samples = set(c_gdsc.index).intersection(cnv_abs.index), set(c_gdsc).intersection(cnv_abs)
print(len(genes), len(samples))


# -
plot_df = pd.concat([
    (cnv_abs > 3).sum().rename('cnv'),
    ploidy.rename('ploidy')
], axis=1).dropna()

g = sns.jointplot('cnv', 'ploidy', data=plot_df, color=bipal_dbgd[0], joint_kws={'edgecolor': 'white', 'lw': .3}, space=0)
g.set_axis_labels('# gene with copy-number > 3', 'Cell line ploidy')
plt.show()

plt.gcf().set_size_inches(3, 3)
plt.savefig('reports/ploidy_cnv_jointplot.png', bbox_inches='tight', dpi=600)
plt.close('all')


# -
plot_df = pd.concat([
        pd.concat([
            cnv_abs.loc[nexp[c], c].rename('cnv'),
            fc.loc[nexp[c], c].rename('bias')
        ], axis=1).dropna().assign(sample=c).reset_index().rename(columns={'index': 'gene'})
    for c in c_gdsc if c in nexp and c in cnv_abs
]).dropna()

# plot_df = plot_df.groupby(['sample', 'cnv'])['bias'].mean().reset_index().query('cnv != -1')
# plot_df = plot_df.assign(ploidy=ploidy[plot_df['sample']].values)
plot_df = plot_df.assign(ploidy=cnv_abs.median()[plot_df['sample']].astype(int).values)
plot_df = plot_df.assign(cnv_d=[str(int(i)) if i < 10 else '10+' for i in plot_df['cnv']])

order = natsorted(set(plot_df.query('cnv > 2')['cnv_d']))

ax = plt.gca()
# sns.violinplot('ploidy', 'bias', 'cnv_d', data=plot_df.query('cnv > 2'), hue_order=order, palette='Reds', linewidth=.3, cut=0, ax=ax, scale='width')
sns.boxplot('ploidy', 'bias', 'cnv_d', data=plot_df.query('cnv > 2'), hue_order=order, palette='Reds', linewidth=.3, fliersize=1, ax=ax, notch=True)
# sns.stripplot('ploidy', 'bias', 'cnv_d', data=plot_df.query('cnv > 2'), hue_order=order, palette='Reds', edgecolor='white', linewidth=.1, size=1, split=True, jitter=.4, ax=ax)
plt.axhline(0, lw=.3, c=bipal_dbgd[0], ls='-')
plt.xlabel('Cell line ploidy')
plt.ylabel('CRISPR fold-change (log2)')
plt.title('Non-expressed genes fold-change')

plt.show()

handles = [mpatches.Circle([.0, .0], .25, facecolor=c, label=l) for c, l in zip(*(sns.color_palette('Reds', n_colors=len(order)).as_hex(), order))]
legend = plt.legend(handles=handles, title='Copy-number', prop={'size': 4})
legend.get_title().set_fontsize('4')
plt.gcf().set_size_inches(4, 3)
plt.savefig('reports/ploidy_nexp_bias_boxplot.png', bbox_inches='tight', dpi=600)
plt.close('all')


# -
df = plot_df.groupby(['sample', 'cnv'])['bias'].mean().reset_index().query('cnv > 2')

c_slope = {}
for c in c_gdsc:
    if c in nexp and c in cnv_abs:
        df_ = df.query("sample == '%s'" % c)[['cnv', 'bias']]
        if df_.shape[0] > 1:
            x, y = zip(*(df_.values))
            lm = LinearRegression().fit(np.matrix(x).T, np.array(y))
            c_slope[c] = lm.coef_[0]
df = pd.concat([pd.Series(c_slope).rename('slope'), ploidy.rename('ploidy')], axis=1).dropna()

sns.jointplot('slope', 'ploidy', data=df)
plt.show()


# -
df = pd.concat([
    c_gdsc.loc[genes, samples].unstack().rename('crispr'),
    cnv_abs.loc[genes, samples].unstack().rename('cnv')
], axis=1).dropna().query('cnv != -1')
df = df.reset_index().rename(columns={'level_0': 'sample', 'level_1': 'gene'})
df = df.assign(chr=sgrna_lib.groupby('GENES')['CHRM'].first()[df['gene']].values)

# chr_cnv = df.groupby(['sample', 'chr'])['cnv'].median()
# df = df.assign(chr_cnv=cnv_seg_c.loc[[(s, c) for s, c in df[['sample', 'chr']].values]].values)
chr_cnv = df.groupby(['sample', 'chr'])['cnv'].median()
df = df.assign(chr_cnv=chr_cnv.loc[[(s, c) for s, c in df[['sample', 'chr']].values]].values)

df = df.assign(ploidy=ploidy[df['sample']].values)

#
plot_df = df.groupby(['sample', 'chr', 'cnv'])[['crispr', 'chr_cnv', 'ploidy']].agg({'crispr': np.mean, 'chr_cnv': 'first', 'ploidy': 'first'}).reset_index()
plot_df = plot_df[~plot_df['chr'].isin(['Y', 'X'])]
plot_df = plot_df.assign(ratio=plot_df['cnv'] / plot_df['chr_cnv'])
plot_df = plot_df.dropna()

g = sns.jointplot('ratio', 'crispr', data=plot_df, kind='reg', color=bipal_dbgd[0], joint_kws={'line_kws': {'color': bipal_dbgd[1]}})
sns.kdeplot(plot_df['ratio'], plot_df['crispr'], ax=g.ax_joint, shade_lowest=False, n_levels=60)
plt.show()

plt.gcf().set_size_inches(3, 3)
plt.savefig('reports/ratio_bias.png', bbox_inches='tight', dpi=600)
plt.close('all')

plot_df_ = pd.concat([
    plot_df[(plot_df['ratio'] < 1) & (plot_df['cnv'] >= 3)].assign(type='depletion (p<1)'),
    plot_df[(plot_df['ratio'] < 3) & (plot_df['ratio'] >= 1) & (plot_df['cnv'] >= 3)].assign(type='duplication (p<3)'),
    plot_df[(plot_df['ratio'] >= 3) & (plot_df['cnv'] >= 3)].assign(type='elongation (p>3)')
])

sns.boxplot('crispr', 'type', data=plot_df_, orient='h', notch=True, color=bipal_dbgd[0], fliersize=1)
plt.show()

plt.xlabel('Crispr mean bias')
plt.ylabel('Chromosome')
plt.gcf().set_size_inches(3, 1)
plt.savefig('reports/ratio_bias_boxplot.png', bbox_inches='tight', dpi=600)
plt.close('all')
