"""Setup for the pylusat package."""

import setuptools
import os

with open('README.md') as f:
    README = f.read()

data_files = []

for item in os.listdir("pylusat/datasets"):
    if not item.startswith("__"):
        data_files.append(os.path.join("datasets", item, "*"))

setuptools.setup(
    name='pylusat',
    author="Changjie Chen",
    author_email="chj.chen@hotmail.com",
    license="BSD",
    description='Python for Land-use suitability analysis tools',
    version='v0.2.2',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/ChangjieChen/pylusat',
    packages=setuptools.find_packages(exclude=("tests",)),
    python_requires=">=3.6",
    install_requires=["geopandas", "rasterio", "rasterstats", "scipy"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    package_data={"pylusat": data_files}
)
