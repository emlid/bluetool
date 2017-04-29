from setuptools import setup, find_packages

setup(
    name='bluetool',
    version='0.2.1',
    license='GPL',
    author='Aleksandr Aleksandrov',
    author_email='aleksandr.aleksandrov@emlid.com',
    url='https://github.com/emlid/bluetool',
    packages=find_packages(),
    install_requires=['tcpbridge']
)
