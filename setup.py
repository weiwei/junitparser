from setuptools import setup, find_packages
import os
import sys

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(name='junitparser',
      version='0.9.0',
      description='Manipulates JUnit/xUnit Result XML files',
      long_description=read('README.rst'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Text Processing',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ],
      url='https://github.com/gastlygem/junitparser',
      author='Joel Wang',
      author_email='gastlygem@gmail.com',
      license='Apache 2.0',
      keywords='junit xunit xml parser',
      packages=find_packages(),
      zip_safe=False)
