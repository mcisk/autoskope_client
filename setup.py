"""Setup script for the Autoskope client library."""

from setuptools import find_packages, setup

setup(
    name="autoskope_client",
    version="1.2.0",
    description="Python client library for the Autoskope API.",
    author="Nico Liebeskind",
    author_email="nico@autoskope.de",
    url="https://github.com/mcisk/autoskope_client",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
