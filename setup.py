#!/usr/bin/env python3
"""
VentCompany - Systema upravlinnya proektamy, rozrakhunkiv ta analityky
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ventilation-company",
    version="1.0.0",
    author="Vasha Firma",
    author_email="info@example.com",
    description="Kompleksna systema upravlinnya dlya vyrobnychoi firmy z ventylyatsiynykh system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pelekanchik/VentCompany",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vent-firm=main_cli:main",
            "vent-firm-gui=main:run_gui",
        ],
    },
)
