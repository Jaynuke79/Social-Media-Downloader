#!/usr/bin/env python3
"""
Setup script for Social Media Downloader
"""
from setuptools import setup, find_packages
import os

# Get the directory of this file
here = os.path.abspath(os.path.dirname(__file__))

# Read the __init__.py file to get version
def get_version():
    with open(os.path.join(here, 'smd', '__init__.py'), 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '1.1.12'

# Read README
def get_long_description():
    try:
        with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "A CLI tool for downloading videos from social media platforms"

setup(
    name="social-media-downloader",
    version=get_version(),
    description="A command-line tool to download videos from various social media platforms",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Nayan Das",
    author_email="nayanchandradas@hotmail.com",
    url="https://github.com/Jaynuke79/Social-Media-Downloader",
    packages=find_packages(include=['smd', 'smd.*']),
    python_requires=">=3.10",
    install_requires=[
        "yt-dlp>=2024.1.0",
        "instaloader>=4.11.0", 
        "tqdm>=4.66.0",
        "requests>=2.32.0",
        "ffmpeg-python>=0.2.0",
        "certifi>=2024.2.0",
        "setuptools>=69.0.0",
        "wheel>=0.42.0",
        "pyfiglet>=1.0.0",
        "termcolor>=2.4.0",
        "tabulate>=0.9.0",
        "cryptography>=41.0.0",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
    ],
    extras_require={
        'dev': [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0", 
            "flake8>=7.0.0",
            "black>=24.0.0",
            "mypy>=1.8.0",
            "isort>=5.13.0",
            "pre-commit>=3.6.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'smd=smd.downloader:cli',
            'social-media-downloader=smd.downloader:cli',
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    keywords="video downloader, social media, youtube, tiktok, instagram, cli",
    license="MIT",
    include_package_data=True,
)