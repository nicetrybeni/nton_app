from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in nton_app/__init__.py
from nton_app import __version__ as version

setup(
	name="nton_app",
	version=version,
	description="Nature to Nurture App with Frappe",
	author="Raya",
	author_email="lbencio@rayasolutionsph.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
