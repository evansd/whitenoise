import ast
import codecs
import os
import re
import sys
from setuptools import setup, find_packages


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
VERSION_RE = re.compile(r'__version__\s+=\s+(.*)')

required_packages = []
if sys.version_info[:2] == (2, 6):
    required_packages.append('argparse')

def read(*path):
    full_path = os.path.join(PROJECT_ROOT, *path)
    with codecs.open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


version_string = VERSION_RE.search(read('whitenoise/__init__.py')).group(1)
version = str(ast.literal_eval(version_string))


setup(
    name='whitenoise',
    version=version,
    author='David Evans',
    author_email='d@evans.io',
    url='http://whitenoise.evans.io',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description="Radically simplified static file serving for WSGI applications",
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Framework :: Django',
        'Framework :: Django :: 1.4',
        'Framework :: Django :: 1.5',
        'Framework :: Django :: 1.6',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=required_packages,
)
