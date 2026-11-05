from setuptools import find_packages, setup

setup(name="legacy-lib", version="1.0.0", packages=find_packages("src"), package_dir={"": "src"}, python_requires=">=3.9")
