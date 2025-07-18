#!/usr/bin/env python3
"""
Setup script for Pisarz - Writing Application
"""

from setuptools import setup, find_packages
import os

# Read long description from README
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
try:
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Pisarz - A comprehensive writing application with advanced features"

# Read requirements
def parse_requirements(filename):
    """Parse requirements from requirements.txt"""
    requirements = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove version constraints for setuptools
                if '>=' in line:
                    package = line.split('>=')[0]
                    requirements.append(package)
                else:
                    requirements.append(line)
    return requirements

requirements = parse_requirements('requirements.txt')

setup(
    name="pisarz",
    version="1.0.0",
    author="Pisarz Team",
    author_email="contact@pisarz.app",
    description="A comprehensive writing application with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pisarz",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Processing :: Markup",
        "Topic :: Office/Business :: Office Suites",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pisarz=main:main',
        ],
        'gui_scripts': [
            'pisarz-gui=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'i18n': ['locales/*/LC_MESSAGES/*.mo', 'locales/*/LC_MESSAGES/*.po'],
        'templates': ['*.j2', '*.yaml'],
        'ui': ['llm/*.qml'],
    },
    zip_safe=False,
    keywords="writing editor text richtext rtf llm ai assistant",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pisarz/issues",
        "Source": "https://github.com/yourusername/pisarz",
    },
)