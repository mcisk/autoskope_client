"""Setup script for the Autoskope client library."""

from setuptools import find_packages, setup

setup(
    name="autoskope_client",
    version="1.4.0",
    description="Python client library for the Autoskope API.",
    author="Nico Liebeskind",
    author_email="nico@autoskope.de",
    url="https://github.com/mcisk/autoskope_client",
    packages=find_packages(),
    package_data={
        "autoskope_client": ["py.typed"],
    },
    install_requires=[
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "python-dotenv>=0.19.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    license="Apache-2.0",
)
