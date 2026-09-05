#!/usr/bin/env python
import os

from setuptools import find_packages, setup

PROJECT_DIR = os.path.dirname(__file__)

setup(
    name="coveredon-test",
    version="1.0.0",
    description="Covered On minimal test plugin for Baserow 2.3.3",
    platforms=["linux"],
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    install_requires=[],
)
