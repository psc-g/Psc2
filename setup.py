"""Setup script for Psc2.

This script will install Psc2 as a Python module.
"""

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="psc2",
    version="0.0.1",
    author="Pablo Samuel Castro",
    author_email="pablosamuelcastro@gmail.com",
    description="Code used to play with Psc2",
    long_description=long_description,
    url="https://github.com/psc-g/Psc2",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
