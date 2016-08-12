#-*- coding: utf-8 -*-
# Copyright (C) 2015-2016 by Brendt Wohlberg <brendt@ieee.org>
# All rights reserved. BSD 3-clause License.
# This file is part of the SPORCO package. Details of the copyright
# and user license can be found in the 'LICENSE.txt' file distributed
# with the package.

"""Dictionary learning based on BPDN sparse coding"""

from __future__ import print_function
from __future__ import absolute_import
from builtins import range
from builtins import object

import numpy as np
from scipy import linalg
import collections
import copy

from sporco import cdict
from sporco import util
from sporco.util import u
from sporco.admm import bpdn
from sporco.admm import cmod
from sporco.admm import dictlrn

__author__ = """Brendt Wohlberg <brendt@ieee.org>"""


class BPDNDictLearn(dictlrn.DictLearn):
    """Dictionary learning based on BPDN and CnstrMOD

    Solve the optimisation problem

    .. math::
       \mathrm{argmin}_{D, X} \;
       (1/2) \| D X - S \|_F^2 + \lambda \| X \|_1 \quad \\text{such that}
       \quad \|\mathbf{d}_m\|_2 = 1

    via interleaved alternation between the ADMM steps of the
    :class:`.BPDN` and :class:`.CnstrMOD` problems.

    After termination of the :meth:`solve` method, attribute :attr:`itstat` is
    a list of tuples representing statistics of each iteration. The
    fields of the named tuple ``IterationStats`` are:

       ``Iter`` : Iteration number

       ``ObjFun`` : Objective function value

       ``DFid`` :  Value of data fidelity term \
       :math:`(1/2) \| D X - S \|_F^2`

       ``RegL1`` : Value of regularisation term \
       :math:`\| X \|_1`

       ``Cnstr`` : Constraint violation measure

       ``XPrRsdl`` : Norm of X primal residual

       ``XDlRsdl`` : Norm of X dual residual

       ``XRho`` : X penalty parameter

       ``DPrRsdl`` : Norm of D primal residual

       ``DDlRsdl`` : Norm of D dual residual

       ``DRho`` : D penalty parameter

       ``Time`` : Cumulative run time
    """


    class Options(dictlrn.DictLearn.Options):
        """BPDN dictionary learning algorithm options.

        Options:

          ``Verbose`` : Flag determining whether iteration status is displayed.

          ``StatusHeader`` : Flag determining whether status header and \
          separator are dislayed

          ``MaxMainIter`` : Maximum main iterations

          ``BPDN`` : Options :class:`sporco.admm.bpdn.BPDN.Options`

          ``CMOD`` : Options :class:`sporco.admm.cmod.CnstrMOD.Options`
        """

        defaults = {'Verbose' : False, 'StatusHeader' : True,
                    'MaxMainIter' : 1000,
                    'BPDN' : copy.deepcopy(bpdn.BPDN.Options.defaults),
                    'CMOD' : copy.deepcopy(cmod.CnstrMOD.Options.defaults)}


        def __init__(self, opt=None):
            """Initialise BPDN dictionary learning algorithm options."""

            dictlrn.DictLearn.Options.__init__(self, {
                'BPDN' : bpdn.BPDN.Options({'MaxMainIter' : 1,
                    'AutoRho' : {'Period' : 10, 'AutoScaling' : False,
                    'RsdlRatio' : 10.0, 'Scaling': 2.0, 'RsdlTarget' : 1.0}}),
                'CMOD' : cmod.CnstrMOD.Options({'MaxMainIter' : 1,
                    'AutoRho' : {'Period' : 10}, 'AuxVarObj' : False})
                })

            if opt is None:
                opt = {}
            self.update(opt)



    def __init__(self, D0, S, lmbda=None, opt=None):
        """
        Initialise a BPDNDictLearn object with problem size and options.

        Parameters
        ----------
        D0 : array_like, shape (N, M)
          Initial dictionary matrix
        S : array_like, shape (N, K)
          Signal vector or matrix
        lmbda : float
          Regularisation parameter
        opt : :class:`BPDNDictLearn.Options` object
          Algorithm options
        """

        if opt is None:
            opt = BPDNDictLearn.Options()
        self.opt = opt

        # Normalise dictionary according to D update options
        D0 = cmod.getPcn(opt['CMOD', 'ZeroMean'])(D0)

        # Modify D update options to include initial values for Y and U
        Nc = D0.shape[1]
        opt['CMOD'].update({'Y0' : D0, 'U0' : np.zeros((S.shape[0], Nc))})

        # Create X update object
        xstep = bpdn.BPDN(D0, S, lmbda, opt['BPDN'])

        # Create D update object
        Nm = S.shape[1]
        dstep = cmod.CnstrMOD(xstep.Y, S, (Nc, Nm), opt['CMOD'])

        # Configure iteration statistics reporting
        isc = dictlrn.IterStatsConfig(
            isfld = ['Iter', 'ObjFun', 'DFid', 'RegL1', 'Cnstr', 'XPrRsdl',
                     'XDlRsdl', 'XRho', 'DPrRsdl', 'DDlRsdl', 'DRho', 'Time'],
            isxmap = {'ObjFun' : 'ObjFun', 'DFid' : 'DFid', 'RegL1' : 'RegL1',
                      'XPrRsdl' : 'PrimalRsdl', 'XDlRsdl' : 'DualRsdl',
                      'XRho' : 'Rho'},
            isdmap = {'Cnstr' :  'Cnstr', 'DPrRsdl' : 'PrimalRsdl',
                      'DDlRsdl' : 'DualRsdl', 'DRho' : 'Rho'},
            evlmap = {},
            hdrtxt = ['Itn', 'Fnc', 'DFid', 'l1', 'Cnstr', 'r_X', 's_X',
                      u('ρ_X'), 'r_D', 's_D', u('ρ_D')],
            hdrmap = {'Itn' : 'Iter', 'Fnc' : 'ObjFun', 'DFid' : 'DFid',
                      'l1' : 'RegL1', 'Cnstr' : 'Cnstr', 'r_X' : 'XPrRsdl',
                      's_X' : 'XDlRsdl', u('ρ_X') : 'XRho', 'r_D' : 'DPrRsdl',
                      's_D' : 'DDlRsdl', u('ρ_D') : 'DRho'}
            )

        # Call parent constructor
        super(BPDNDictLearn, self).__init__(xstep, dstep, opt, isc)
