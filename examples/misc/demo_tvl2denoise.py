#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Copyright (C) 2015-2016 by Brendt Wohlberg <brendt@ieee.org>
# All rights reserved. BSD 3-clause License.
# This file is part of the SPORCO package. Details of the copyright
# and user license can be found in the 'LICENSE.txt' file distributed
# with the package.

"""Basic tvl2.TVL2Denoise usage example"""

from __future__ import print_function
from builtins import input
from builtins import range

import numpy as np

from sporco import util
from sporco import plot
from sporco.admm import tvl2


# Load demo image and construct noisy test image
img = util.ExampleImages().image('lena.grey', scaled=True)
np.random.seed(12345)
imgn = img + np.random.normal(0.0, 0.04, img.shape)

# Set up TVL2Denoise options
lmbda = 0.04
opt = tvl2.TVL2Denoise.Options({'Verbose' : True, 'MaxMainIter' : 200,
                                'gEvalY' : False})

# Initialise and run TVL2Denoise object
b = tvl2.TVL2Denoise(imgn, lmbda, opt)
b.solve()
print("TVL2Denoise solve time: %.2fs" % b.runtime)


# Display input and result image
fig1 = plot.figure(1, figsize=(14,7))
plot.subplot(1,2,1)
plot.imview(imgn, fgrf=fig1, title='Noisy')
plot.subplot(1,2,2)
plot.imview(b.X, fgrf=fig1, title='l2-TV Result')
fig1.show()


# Plot functional value, residuals, and rho
its = b.getitstat()
fig2 = plot.figure(2, figsize=(21,7))
plot.subplot(1,3,1)
plot.plot(its.ObjFun, fgrf=fig2, xlbl='Iterations', ylbl='Functional')
plot.subplot(1,3,2)
plot.plot(np.vstack((its.PrimalRsdl, its.DualRsdl)).T, fgrf=fig2,
          ptyp='semilogy', xlbl='Iterations', ylbl='Residual',
          lgnd=['Primal', 'Dual']);
plot.subplot(1,3,3)
plot.plot(its.Rho, fgrf=fig2, xlbl='Iterations', ylbl='Penalty Parameter')
fig2.show()


# Wait for enter on keyboard
input()

