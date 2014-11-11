#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration(None, parent_package, top_path)
    config.add_subpackage('fastdm')
    return config

def main():
    print "YOO"
    from numpy.distutils.core import setup
    setup(name='fastdm',
          version='0.1',
          description='Python wrapper for fast-dm',
          author='Gilles de Hollander',
          author_email='g.dehollander@uva.nl',
          url='http://www.gillesdehollander.nl',
          packages=['fastdm'],
          configuration=configuration
         )

if __name__ == '__main__':
    main()
