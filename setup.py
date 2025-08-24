#!/usr/bin/env python3
"""
Setup script for Watercooler Manager
"""

from setuptools import setup, find_packages
import os

# Read version from __init__.py
def get_version():
    version_file = os.path.join("src", "watercooler_manager", "__init__.py")
    with open(version_file, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

# Read README for long description
def get_long_description():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    return "System tray application for managing LCT water coolers"

setup(
    name="watercooler-manager",
    version=get_version(),
    description="System tray application for managing LCT water coolers",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Allan Ditzel",
    author_email="allan@allanditzel.com",
    url="https://github.com/tomups/watercooler-manager",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "watercooler_manager": ["../icons/*.png"],
    },
    include_package_data=True,
    
    # Entry points
    entry_points={
        "console_scripts": [
            "watercooler-manager=watercooler_manager:main",
            "watercooler-manager-gui=watercooler_manager.gui_client:main",
        ],
    },
    
    # Dependencies - Updated based on Python lifecycle (3.8 is EOL)
    python_requires=">=3.9",
    install_requires=[
        "bleak>=0.22.0",
        "pillow>=11.0.0",
        "pystray>=0.19.0",
        "six>=1.17.0",
        "typing_extensions>=4.12.0",
    ],
    
    # Linux-specific dependencies
    extras_require={
        "linux": [
            "PyGObject>=3.42.0",
            "pycairo>=1.20.0",
        ],
    },
    
    # Metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    keywords="watercooler bluetooth system-tray hardware cooling",
    project_urls={
        "Bug Reports": "https://github.com/tomups/watercooler-manager/issues",
        "Source": "https://github.com/tomups/watercooler-manager",
    },
)
