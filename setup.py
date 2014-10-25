#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

VERSION = "1.0.8"
AUTHORS = '''\
Olof Bjarnason, Fredrik Wendt, Krunoslav Saho,
Samuel Ytterbrink, Rafael Capucho, Ilian Iliev,
Henrik Bohre, Wari Wahab, Maximilien Riehl,
Javier J. Gutiérrez'''
HOMEPAGE = "http://pytddmon.org"

if __name__ == '__main__':
    setup(
        name='pytddmon',
        version=VERSION,
        description='continuous unit testing in Python',
        long_description='Read the pytddmon blog and more documentation at ' +
                         'http://pytddmon.org',
        author=AUTHORS,
        author_email="olof.bjarnason@gmail.com",
        license='MIT',
        url=HOMEPAGE,
        scripts=['src/pytddmon.py'],
        test_suite='nose.collector',
        zip_safe=True
    )
