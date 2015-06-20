import os
import codecs
from setuptools import setup, find_packages


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def read(*path):
    full_path = os.path.join(PROJECT_ROOT, *path)
    with codecs.open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='whitenoise',
    version='2.0',
    author='David Evans',
    author_email='d@evans.io',
    url='http://whitenoise.evans.io',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description="Radically simplified static file serving for WSGI applications",
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
