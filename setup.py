from setuptools import setup, find_packages, Extension
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name="commcooking",
    version="0.1.1",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.5',
    scripts=['bin/gen_comm_cooking_invens','bin/osm_comm_cooking'],
    setup_requires=['geopandas>=0.14.0','pandas>=2.1.0','pyrosm>=0.6.2'],
    install_requires=['geopandas>=0.14.0','pandas>=2.1.0','pyrosm>=0.6.2'],
    package_data={'commcooking': ['examples/*.csv','examples/*.lst','data/*.csv']},
    author_email='beidler.james@epa.gov'
)
