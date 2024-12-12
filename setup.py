from setuptools import setup, find_packages

setup(
    name = 'googledrive',
    version = '0.1',
    packages = find_packages(),
    install_requires=['slepy>=0.1', 'polars>=1.17.1', "google-api-python-client>=2.155.0", "google-auth-httplib2>=0.2.0", "google-auth-oauthlib>=1.2.1"],
)
