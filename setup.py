from setuptools import setup, find_packages

setup(
    name='chittorgarh_client',
    version='0.1.1',
    author='Dhaval Mehta',
    description='Unofficial chittorgarh.com client',
    long_description='Unofficial chittorgarh client',
    url='https://github.com/dhaval-mehta/chittorgarh-client',
    keywords='chittorgarh',
    python_requires='>=3.7, <4',
    packages=find_packages(include=['chittorgarh_client']),
    install_requires=[
        'requests',
        'lxml',
    ],
)