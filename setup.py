#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Chump - by Snailwhale LLP
# All code copyright (c) 2010-2012, Snailwhale LLP. All rights reserved.

from setuptools import setup, find_packages

from chump import __version__

long_description = """Chump - A utility HTML parser"""

setup(
	name='Chump',
	version=__version__,
	description='Chump HTML Parser',
	long_description=long_description,
	author='Snailwhale LLP',
	author_email='code@deploycms.com',
	url='http://deploycms.com/',
	download_url='http://code.deploycms.com/',
	license='Private',
	platforms=['Linux',],
	classifiers=[
		'Environment :: Web Environment',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
	],
	zip_safe=False,
	packages=find_packages(exclude=['tests',]),
)
