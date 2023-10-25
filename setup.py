from setuptools import setup, find_packages

setup(
    name='app-name',
    version='0.1',
    author='Dhaval Mehta',
    description='Unofficial chittorgarh.com client',
    long_description='Unofficial chittorgarh.com client',
    url='https://github.com/dhaval-mehta/chittorgarh-client',
    keywords='development, setup, setuptools',
    python_requires='>=3.7, <4',
    packages=find_packages(include=['chittorgarh-client', 'chittorgarh-client.*']),
    install_requires=[
        'requests',
        'lxml',
    ],
)