#!/usr/bin/env python

from setuptools import setup

if __name__ == '__main__':
    setup(
        name='pytddmon',
        version='1.0.0',
        description='continuous unit testing in Python',
        long_description='Read the pytddmon blog and more documentation at http://pytddmon.org',
        author='''Olof Bjarnason, Fredrik Wendt, Krunoslav Saho,
Samuel Ytterbrink, Rafael Capucho, Ilian Iliev, Henrik Bohre, Wari Wahab''',
        author_email="olof.bjarnason@gmail.com",
        license='MIT',
        url='https://github.com/objarni/pytddmon',
        scripts=['src/pytddmon.py'],
        test_suite='nose.collector',
        zip_safe=True
    )
