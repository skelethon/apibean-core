#!/usr/bin/env python

import setuptools

setuptools.setup(
  name = 'apibean-core',
  version = '0.0.2-alpha02',
  description = 'A simple API wrapper',
  author = 'skelethon',
  license = 'GPL-3.0',
  url = 'https://github.com/skelethon/apibean-core',
  download_url = 'https://github.com/skelethon/apibean-core/downloads',
  keywords = ['restful-api'],
  classifiers = [],
  install_requires = open("requirements.txt").readlines(),
  python_requires=">=3.8",
  package_dir = {'':'src'},
  packages = setuptools.find_packages('src'),
)
