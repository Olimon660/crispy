#!/usr/bin/env python
# Copyright (C) 2019 Emanuel Goncalves

import sys
import logging
import seaborn as sns
from crispy.Utils import Utils, SSGSEA
from crispy.CrispyPlot import CrispyPlot
from crispy.QCPlot import QCplot, GSEAplot
from crispy.CopyNumberCorrection import Crispy, CrispyGaussian


__version__ = "0.3.0"

# - SET STYLE
sns.set(
    style="ticks",
    context="paper",
    font_scale=0.75,
    font="sans-serif",
    rc=CrispyPlot.SNS_RC,
)

# - Logging
__name__ = "Crispy"

logger = logging.getLogger(__name__)

if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("[%(asctime)s - %(levelname)s]: %(message)s"))
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# - HANDLES
__all__ = [
    "Crispy",
    "CrispyGaussian",
    "QCplot",
    "CrispyPlot",
    "SSGSEA",
    "GSEAplot",
    "Utils",
    "__version__"
]
