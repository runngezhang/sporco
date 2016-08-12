#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Copyright (C) 2015-2016 by Brendt Wohlberg <brendt@ieee.org>
# All rights reserved. BSD 3-clause License.
# This file is part of the SPORCO package. Details of the copyright
# and user license can be found in the 'LICENSE.txt' file distributed
# with the package.

"""Basic spline.SplineL1 usage example"""

from __future__ import print_function
from builtins import input
from builtins import range

import numpy as np
import matplotlib.pyplot as plt

from sporco import util
from sporco.admm import spline


# Load demo image
img = util.ExampleImages().image('lena.grey', scaled=True)
np.random.seed(12345)
imgn = util.spnoise(img, 0.2)


# Set up SplineL1 options
lmbda = 4.0
opt = spline.SplineL1.Options({'Verbose' : True, 'gEvalY' : False})


# Initialise and run SplineL1 object
b = spline.SplineL1(imgn, lmbda, opt)
b.solve()
print("SplineL1 solve time: %.2fs" % b.runtime)


# Display input and result image
fig1 = plt.figure(1, figsize=(14,7))
plt.subplot(1,2,1)
util.imview(imgn, fgrf=fig1, title='Noisy')
plt.subplot(1,2,2)
util.imview(b.X, fgrf=fig1, title='l1-Spline Result')
fig1.show()


# Plot functional value, residuals, and rho
its = b.getitstat()
fig2 = plt.figure(2, figsize=(21,7))
plt.subplot(1,3,1)
util.plot(its.ObjFun, fgrf=fig2, ptyp='semilogy', xlbl='Iterations',
          ylbl='Functional')
plt.subplot(1,3,2)
util.plot(np.vstack((its.PrimalRsdl, its.DualRsdl)).T, fgrf=fig2,
          ptyp='semilogy', xlbl='Iterations', ylbl='Residual',
          lgnd=['Primal', 'Dual']);
plt.subplot(1,3,3)
util.plot(its.Rho, fgrf=fig2, xlbl='Iterations', ylbl='Penalty Parameter')
fig2.show()


# Wait for enter on keyboard
input()

