#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

authors = '''\
Olof Bjarnason, Fredrik Wendt, Krunoslav Saho,
Samuel Ytterbrink, Rafael Capucho, Ilian Iliev,
Henrik Bohre, Wari Wahab, Maximilien Riehl,
Javier J. Gutiérrez'''

if __name__ == '__main__':
    setup(
        name='pytddmon',
        version='1.0.5',
        description='continuous unit testing in Python',
        long_description='Read the pytddmon blog and more documentation at http://pytddmon.org',
        author=authors,
        author_email="olof.bjarnason@gmail.com",
        license='MIT',
        url='http://pytddmon.org',
        scripts=['src/pytddmon.py'],
        test_suite='nose.collector',
        zip_safe=True
    )
