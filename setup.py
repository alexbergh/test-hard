#!/usr/bin/env python3
"""
Setup script for test-hard platform.

For modern installations, prefer using pyproject.toml:
    pip install -e .

This setup.py is provided for backward compatibility.
"""

from setuptools import setup

# Read version from VERSION file
with open("VERSION", "r", encoding="utf-8") as f:
    version = f.read().strip()

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="test-hard",
    version=version,
    description="Security hardening and monitoring platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="alexbergh",
    author_email="alex@example.com",
    url="https://github.com/alexbergh/test-hard",
    project_urls={
        "Documentation": "https://github.com/alexbergh/test-hard/tree/main/docs",
        "Source": "https://github.com/alexbergh/test-hard",
        "Issues": "https://github.com/alexbergh/test-hard/issues",
        "Changelog": "https://github.com/alexbergh/test-hard/blob/main/CHANGELOG.md",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: Security",
    ],
    keywords="security hardening monitoring prometheus grafana docker",
    python_requires=">=3.11",
    # Configuration is read from pyproject.toml
    # This setup.py is for compatibility only
)
