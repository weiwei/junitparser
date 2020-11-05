from setuptools import setup, find_packages
import os

from junitparser import version

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(name='junitparser',
      version=version,
      description='Manipulates JUnit/xUnit Result XML files',
      long_description=read('README.rst'),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Text Processing',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
      ],
      url='https://github.com/weiwei/junitparser',
      author='Weiwei Wang',
      author_email='gastlygem@gmail.com',
      license='Apache 2.0',
      install_requires=['future'],
      keywords='junit xunit xml parser',
      packages=find_packages(exclude=['tests']),
      entry_points={
          'console_scripts': [
              'junitparser=junitparser.cli:main'
          ]
      },
      zip_safe=False)
