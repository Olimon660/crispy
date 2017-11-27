#!/usr/bin/env python
# Copyright (C) 2017 Emanuel Goncalves

import pickle
import numpy as np
import pandas as pd
import seaborn as sns
from natsort import natsorted
import matplotlib.pyplot as plt

# - Imports
# Non-expressed genes
nexp = pickle.load(open('data/gdsc/nexp_pickle.pickle', 'rb'))

# sgRNA library
sgrna_lib = pd.read_csv('data/gdsc/crispr/KY_Library_v1.1_annotated.csv', index_col=0).dropna(subset=['STARTpos', 'GENES'])

# CRISPR fold-changes
fc = pd.read_csv('data/gdsc/crispr/crispy_gdsc_fold_change_sgrna.csv', index_col=0)
fc = fc.groupby(sgrna_lib.loc[fc.index, 'GENES']).mean().dropna()

# Copy-number absolute counts
cnv = pd.read_csv('data/gdsc/copynumber/Gene_level_CN.txt', sep='\t', index_col=0)
cnv = cnv.loc[:, cnv.columns.isin(list(fc))]
cnv_abs = cnv.applymap(lambda v: int(v.split(',')[1]))


# -
genes, samples = set(cnv_abs.index).intersection(fc.index), set(cnv).intersection(fc)

df = pd.concat([
    fc.loc[genes, samples].unstack().rename('crispr'),
    cnv_abs.loc[genes, samples].unstack().rename('cnv')
], axis=1).dropna().reset_index().rename(columns={'level_0': 'sample'})
df = df.assign(chr=sgrna_lib.groupby('GENES')['CHRM'].first().rename('chr').loc[df['GENES']].values)
df = df.query('cnv != -1')
df = df.assign(cnv_d=['%d' % i if i < 8 else '>=8' for i in df['cnv']])

plot_df = pd.pivot_table(df, index='sample', columns='cnv_d', values='crispr', aggfunc='mean')
plot_df = plot_df.loc[:, natsorted(set(df['cnv_d']))]

sns.set(style='white', font_scale=.75)
g = sns.heatmap(plot_df.T, mask=plot_df.T.isnull(), cmap='RdYlBu', lw=.3, center=0, square=True, cbar=False)
g.set_xlabel('')
g.set_ylabel('Copy-number')
plt.setp(g.get_yticklabels(), rotation=0)
plt.gcf().set_size_inches(18, 6)
plt.savefig('reports/crispr_chr_effects_all_samples.png', bbox_inches='tight', dpi=600)
plt.close('all')


sns.factorplot('cnv_d', 'crispr', 'sample', data=df)
plt.gcf().set_size_inches(4, 2)
plt.savefig('reports/copy_number_effect_samples.png', bbox_inches='tight', dpi=600)
plt.close('all')