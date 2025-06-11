from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define data files
data_files = [
    ('share/applications', ['files/io.github.Cookiiieee.WSelector.desktop']),
    ('share/metainfo', ['io.github.Cookiiieee.WSelector.metainfo.xml']),
]

# Add all icon sizes
icon_sizes = ['16x16', '24x24', '32x32', '48x48', '64x64', '128x128', '256x256', '512x512']
for size in icon_sizes:
    icon_path = f'icons/hicolor/{size}/apps/io.github.Cookiiieee.WSelector.png'
    if os.path.exists(icon_path):
        data_files.append((f'share/icons/hicolor/{size}/apps', [icon_path]))

setup(
    name="wselector",
    version="0.2.0",
    author="Cookiiieee",
    description="A modern GTK4/Adwaita application for browsing, downloading, and setting wallpapers from Wallhaven.cc",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cookiiieee/WSelector",
    packages=find_packages(),
    package_data={
        'wselector': ['*.ui', '*.css', '*.png'],  # Include any UI files, styles, or images
    },
    data_files=data_files,
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
            'wselector=wselector.__main__:main',
        ],
    },
)