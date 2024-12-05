from setuptools import setup, find_packages

setup(
    name="svcs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pathlib==1.0.1",
        "PyYAML==6.0.1",
        "python-dateutil==2.8.2"
    ],
    entry_points={
        'console_scripts': [
            'svcs=svcs.__main__:main',
        ],
    },
)
