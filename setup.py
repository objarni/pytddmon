#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

from src.pytddmon import VERSION, AUTHORS, HOMEPAGE

if __name__ == '__main__':
    setup(
        name='pytddmon',
        version=VERSION,
        description='continuous unit testing in Python',
        long_description='Read the pytddmon blog and more documentation at http://pytddmon.org',
        author=AUTHORS,
        author_email="olof.bjarnason@gmail.com",
        license='MIT',
        url=HOMEPAGE,
        scripts=['src/pytddmon.py'],
        test_suite='nose.collector',
        zip_safe=True
    )
