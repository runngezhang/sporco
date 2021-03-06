#-*- coding: utf-8 -*-
# Copyright (C) 2015-2016 by Brendt Wohlberg <brendt@ieee.org>
# All rights reserved. BSD 3-clause License.
# This file is part of the SPORCO package. Details of the copyright
# and user license can be found in the 'LICENSE.txt' file distributed
# with the package.

"""Dictionary learning based on ADMM sparse coding and dictionary updates"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from builtins import range
from builtins import object

import collections

from sporco import cdict
from sporco import util
from sporco.util import u

__author__ = """Brendt Wohlberg <brendt@ieee.org>"""



class IterStatsConfig(object):
    """Configuration object for general dictionary learning algorithm
    iteration statistics.
    """

    fwiter = 4
    """Field width for iteration count display column"""
    fpothr = 2
    """Field precision for other display columns"""


    def __init__(self, isfld, isxmap, isdmap, evlmap, hdrtxt, hdrmap):
        """Initialise configuration object.

        Parameters
        ----------
        isfld : list
          List of field names for iteration statistics namedtuple
        isxmap : dict
          Dictionary mapping iteration statistics namedtuple field names
          to field names in corresponding X step object iteration
          statistics namedtuple
        isdmap : dict
          Dictionary mapping iteration statistics namedtuple field names
          to field names in corresponding D step object iteration
          statistics namedtuple
        evlmap : dict
          Dictionary mapping iteration statistics namedtuple field names
          to labels in the dict returned by :meth:`DictLearn.evaluate`
        hdrtxt : list
          List of column header titles for verbose iteration statistics
          display
        hdrmap : dict
          Dictionary mapping column header titles to IterationStats entries
            """

        self.IterationStats = collections.namedtuple('IterationStats', isfld)
        self.isxmap = isxmap
        self.isdmap = isdmap
        self.evlmap = evlmap
        self.hdrtxt = hdrtxt
        self.hdrmap = hdrmap

        # Call utility function to construct status display formatting
        self.hdrstr, self.fmtstr, self.nsep = util.solve_status_str(
            hdrtxt, type(self).fwiter, type(self).fpothr)



    def iterstats(self, j, t, isx, isd, evl):
        """Construct IterationStats namedtuple from X step and D step
        IterationStats namedtuples.

        Parameters
        ----------
        j : int
          Iteration number
        t : float
          Iteration time
        isx : namedtuple
          IterationStats namedtuple from X step object
        isd : namedtuple
          IterationStats namedtuple from D step object
        evl : dict
          Dict associating result labels with values computed by
          :meth:`DictLearn.evaluate`
        """

        vlst = []
        # Iterate over the fields of the IterationStats namedtuple
        # to be populated with values. If a field name occurs as a
        # key in the isxmap dictionary, use the corresponding key
        # value as a field name in the isx namedtuple for the X
        # step object and append the value of that field as the
        # next value in the IterationStats namedtuple under
        # construction. The isdmap dictionary is handled
        # correspondingly with respect to the isd namedtuple for
        # the D step object. There are also two reserved field
        # names, 'Iter' and 'Time', referring respectively to the
        # iteration number and run time of the dictionary learning
        # algorithm.
        for fnm in self.IterationStats._fields:
            if fnm in self.isxmap:
                vlst.append(getattr(isx, self.isxmap[fnm]))
            elif fnm in self.isdmap:
                vlst.append(getattr(isd, self.isdmap[fnm]))
            elif fnm in self.evlmap:
                vlst.append(evl[fnm])
            elif fnm == 'Iter':
                vlst.append(j)
            elif fnm == 'Time':
                vlst.append(t)
            else:
                vlst.append(None)

        return self.IterationStats._make(vlst)



    def printheader(self):
        """Print status display header and separator strings."""

        print(self.hdrstr)
        self.printseparator()



    def printseparator(self):
        "Print status display separator string."""

        print("-" * self.nsep)



    def printiterstats(self, itst):
        """Print iteration statistics.

        Parameters
        ----------
        itst : namedtuple
          IterationStats namedtuple as returned by :meth:`iterstats`
        """

        itdsp = tuple([getattr(itst, self.hdrmap[col]) for col in self.hdrtxt])
        print(self.fmtstr % itdsp)




class DictLearn(object):
    """General dictionary learning class that supports alternation
    between user-specified sparse coding and dictionary update steps,
    each of which is based on an ADMM algorithm.
    """


    class Options(cdict.ConstrainedDict):
        """General dictionary learning algorithm options.

        Options:

          ``Verbose`` : Flag determining whether iteration status is displayed.

          ``StatusHeader`` : Flag determining whether status header and \
           separator are displayed

          ``MaxMainIter`` : Maximum main iterations
        """

        defaults = {'Verbose' : False, 'StatusHeader' : True,
                    'MaxMainIter' : 1000}


        def __init__(self, opt=None):
            """Initialise flexible dictionary learning algorithm options."""

            if opt is None:
                opt = {}
            cdict.ConstrainedDict.__init__(self, opt)




    def __init__(self, xstep, dstep, opt=None, isc=None):
        """
        Initialise a DictLearn object with problem size and options.

        Parameters
        ----------
        xstep : bpdn (or similar interface) object
          Object handling X update step
        dstep : cmod (or similar interface) object
          Object handling D update step
        opt : :class:`DictLearn.Options` object
          Algorithm options
        isc : :class:`DictLearn.IterStatsConfig` object
          Iteration statistics and header display configuration
        """

        self.runtime = 0.0
        self.timer = util.Timer()

        if opt is None:
            opt = DictLearn.Options()
        self.opt = opt

        if isc is None:
            isc = IterStatsConfig(
                isfld = ['Iter', 'ObjFunX', 'XPrRsdl', 'XDlRsdl', 'XRho',
                         'ObjFunD', 'DPrRsdl', 'DDlRsdl', 'DRho', 'Time'],
                isxmap = {'ObjFunX' : 'ObjFun', 'XPrRsdl' : 'PrimalRsdl',
                          'XDlRsdl' : 'DualRsdl', 'XRho' : 'Rho'},
                isdmap = {'ObjFunD' : 'DFid', 'DPrRsdl' : 'PrimalRsdl',
                          'DDlRsdl' : 'DualRsdl', 'DRho' : 'Rho'},
                evlmap = {},
                hdrtxt = ['Itn', 'FncX', 'r_X', 's_X', u('ρ_X'),
                          'FncD', 'r_D', 's_D', u('ρ_D')],
                hdrmap = {'Itn' : 'Iter', 'FncX' : 'ObjFunX',
                          'r_X' : 'XPrRsdl', 's_X' : 'XDlRsdl',
                          u('ρ_X') : 'XRho', 'FncD' : 'ObjFunD',
                          'r_D' : 'DPrRsdl', 's_D' : 'DDlRsdl',
                          u('ρ_D') : 'DRho'}
            )
        self.isc = isc

        self.xstep = xstep
        self.dstep = dstep

        self.itstat = []
        self.j = 0

        # Increment `runtime` to reflect object initialisation
        # time. The timer object is reset to avoid double-counting of
        # elapsed time if a similar increment is applied in a derived
        # class __init__.
        self.runtime += self.timer.elapsed(reset=True)



    def solve(self):
        """Run optimisation"""

        # Print header and separator strings
        if self.opt['Verbose'] and self.opt['StatusHeader']:
            self.isc.printheader()

        # Reset timer
        self.timer.start()

        for j in range(self.j, self.j + self.opt['MaxMainIter']):

            # X update
            self.xstep.solve()
            self.dstep.setcoef(self.xstep.getcoef())

            # D update
            self.dstep.solve()
            self.xstep.setdict(self.dstep.getdict())

            # Evaluate progress
            evl = self.evaluate()

            # Record elapsed time
            t = self.timer.elapsed()

            # Extract and record iteration stats
            itst = self.isc.iterstats(j, t, self.xstep.itstat[-1],
                                      self.dstep.itstat[-1], evl)
            self.itstat.append(itst)

            # Display iteration stats if Verbose option enabled
            if self.opt['Verbose']:
                self.isc.printiterstats(itst)


        # Record run time
        self.runtime += self.timer.elapsed()

        # Record iteration count
        self.j = j+1

        # Print final separator string if Verbose option enabled
        if self.opt['Verbose'] and self.opt['StatusHeader']:
            self.isc.printseparator()

        # Return final dictionary
        return self.getdict()



    def evaluate(self):
        """Evaluate results (e.g. functional value) of previous iteration"""

        return None



    def getdict(self):
        """Get final dictionary"""

        return self.dstep.getdict()



    def getcoef(self):
        """Get final coefficient map array"""

        return self.xstep.getcoef()



    def getitstat(self):
        """Get iteration stats as named tuple of arrays instead of array of
        named tuples.
        """

        if len(self.itstat) == 0:
            return None
        else:
            return self.isc.IterationStats(
                *[[self.itstat[k][l] for k in range(len(self.itstat))]
                  for l in range(len(self.itstat[0]))]
            )
