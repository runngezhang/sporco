#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from glob import glob
from setuptools import setup
from distutils.command import build as build_module
import urllib2
import StringIO
import os.path
import numpy as np
import scipy.misc


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def geturlimage(url, timeout=10):
    img = None
    ntry = 0
    while ntry < 3:
        try:
            rspns = urllib2.urlopen(url, timeout=timeout)
            cntnt = rspns.read()
            img = scipy.misc.imread(StringIO.StringIO(cntnt))
            break
        except urllib2.URLError as e:
            ntry += 1
            print type(e)
    return img



class build(build_module.build):
  def run(self):
    
      path = 'sporco/data'
      urllst = {'lena.png' :
                'http://sipi.usc.edu/database/misc/4.2.04.tiff',
                'lena.grey.png' :
                'https://web.archive.org/web/20070328214632/http://decsai.ugr.es/~javier/denoise/lena.png',
                'barbara.png' :
                'http://www.hlevkin.com/TestImages/barbara.bmp',
                'barbara.grey.png' :
                'https://web.archive.org/web/20070209141039/http://decsai.ugr.es/~javier/denoise/barbara.png',
                'mandrill.tif' :
                'http://sipi.usc.edu/database/misc/4.2.03.tiff',
                'man.grey.tif' :
                'http://sipi.usc.edu/database/misc/5.3.01.tiff',
                'kiel.grey.bmp' :
                'http://www.hlevkin.com/TestImages/kiel.bmp'}

      for key in urllst.keys():
          fnm = os.path.splitext(key)[0]
          dst = os.path.join(path, fnm) + '.png'
          if not os.path.isfile(dst):
              print 'Getting %s' % key
              img = geturlimage(urllst[key])
              if img is not None:
                  scipy.misc.imsave(dst, img)
      build_module.build.run(self)
                  


name = 'sporco'
version = '0.0.1'

packages = ['sporco', 'sporco.admm']

docdirbase  = 'share/doc/%s-%s' % (name, version)

data = [(docdirbase, glob("*.txt"))]
dd = os.path.join(docdirbase,'examples')
pp = os.path.join('examples')
data.append((dd, glob(os.path.join(pp ,"*.py"))))

install_requires = ['pyfftw']

longdesc = read('README.rst')
longdesc = longdesc[longdesc.index('==\n\n')+4:]

setup(
    name             = name,
    version          = version,
    description      = 'Sparse Optimisation Research Code',
    long_description = longdesc,
    license          = 'BSD',
    url              = 'http://math.lanl.gov/~brendt/Software/SPORCO/',
    author           = 'Brendt Wohlberg',
    author_email     = 'brendt@ieee.org',
    packages         = packages,
    package_data     = {'sporco': ['data/*.png']},
    data_files       = data,
    include_package_data = True,
    setup_requires   = ['pytest-runner'],
    tests_require    = ['pytest'],
    install_requires = install_requires,
    cmdclass = {
        'build': build
    },
    classifiers = [
    'License :: OSI Approved :: BSD License',
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Scientific/Engineering :: Mathematics',
    ],
    zip_safe = False
)