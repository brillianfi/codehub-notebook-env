#!/opt/conda/bin/python
from setuptools import setup

setup(
    name="cds",
    version="0.0.1",
    author="patient0",
    description="A small example package",
    entry_points={"console_scripts": ["cds=cds.cli:main", "sudocds=cds.sudocli:main"]},
)
