from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wselector",
    version="0.2.0",
    author="Cookiiieee",
    author_email="your.email@example.com",  # Update this
    description="A modern GTK4/Adwaita application for browsing, downloading, and setting wallpapers from Wallhaven.cc",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cookiiieee/WSelector",
    packages=find_packages(),
    package_data={
        'wselector': ['*.ui', '*.css', '*.png'],  # Include any UI files, styles, or images
    },
    install_requires=[
        'PyGObject>=3.42.0',
        'requests>=2.31.0',
        'beautifulsoup4>=4.13.4',
        'psutil>=7.0.0',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment",
    ],
    python_requires='>=3.12',
    entry_points={
        'console_scripts': [
            'wselector=wselector:main',
        ],
    },
)
