'''Setup ML-project'''

from setuptools import setup

version = '0.0.5'

setup(
    name='traffic_disruption',
    version=version,
    author='Mikko Koho',
    py_modules=['apiharvester', 'models'],
    install_requires=[
        'lxml >= 3.1.2',
        'iso8601',
        'requests',
    ],
)
