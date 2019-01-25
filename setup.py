#! /usr/bin/env python

from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='LabEquipment',
      version='0.1',
      description='SMA Receiver Lab Equipment scripts and drivers',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6',
      ],
      keywords='lab equipment, data acquisition, GPIB drivers, receiver',
      url='https://github.com/PaulKGrimes/LabEquipment',
      author='Paul Grimes',
      author_email='pgrimes@cfa.harvard.edu',
      packages=find_packages(),
      install_requires=[
          'pyvisa', 'mcculw', 'hjson', 'jsonmerge', 'numpy', 'matplotlib'
      ],
      include_package_data=True,
      scripts=['LabEquipment/scripts/IV.py', 'LabEquipment/scripts/IVP.py', 'LabEquipment/scripts/IVY.py', 'LabEquipment/scripts/IFP.py', 'LabEquipment/scripts/LoadMover.py'],
      entry_points = {
        'console_scripts': ['IV=LabEquipment.scripts.IV:main',
                            'IVP=LabEquipment.scripts.IVP:main',
                            'IVY=LabEquipment.scripts.IVY:main',
                            'IFP=LabEquipment.scripts.IFP:main',
                            'LoadMover=LabEquipment.scripts.LoadMover:main']
      },
      #test_suite='nose.collector',
      #tests_require=['nose'],
      zip_safe=True)
