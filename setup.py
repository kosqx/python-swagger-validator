#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import with_statement, division, absolute_import


import io
import codecs
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


import swagger_validator


def read(filename):
    with io.open(filename, encoding='utf-8') as f:
        data = f.read()
    return data


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name='swagger_validator',
    version=swagger_validator.__version__,
    url='http://github.com/kosqx/swagger_validator/',
    license='BSD',
    author='Krzysztof Kosyl',
    tests_require=['pytest'],
    install_requires=[],
    cmdclass={'test': PyTest},
    author_email='krzysztof.kosyl@gmail.com',
    description='Swagger Validator',
    long_description=read('README.rst'),
    packages=['swagger_validator'],
    include_package_data=True,
    platforms='any',
    test_suite='swagger_validator.tests.test_swagger_validator',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Testing',
    ],
    extras_require={
        'testing': ['pytest'],
    }
)
