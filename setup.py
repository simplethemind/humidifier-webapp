from setuptools import find_packages, setup

setup(
    name='humidifier-webapp',
    version='0.2a2',
    author='Sabin Serban',
    description='Webapp to communicate with and control humidifier-controller serial server. Server must be running before webapp starts.',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'pandas',
        'numpy',
        'matplotlib',
        'mpld3',
        'Pyro5'
    ],
)