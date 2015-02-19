'''Setup ML-project'''

from setuptools import setup

version = '0.0.3'

setup(
    name='ML-project',
    version=version,
    author='Mikko Koho',
    py_modules=['apiharvester'],
    install_requires=[
        'lxml >= 3.1.2',
        'iso8601',
        'requests',
    ],
)
