from setuptools import setup, find_packages
import os
import sys

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(name='junitparser',
      version="1.4.1",
      description='Manipulates JUnit/xUnit Result XML files',
      long_description=read('README.rst'),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Text Processing',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      url='https://github.com/gastlygem/junitparser',
      author='Joel Wang',
      author_email='gastlygem@gmail.com',
      license='Apache 2.0',
      install_requires=['future'],
      keywords='junit xunit xml parser',
      packages=find_packages(),
      scripts=['bin/junitparser'],
      zip_safe=False)
