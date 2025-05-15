from setuptools import setup, find_packages

setup(
    name="autoskope_client",
    version="0.1.0",
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