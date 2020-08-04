import ast
import codecs
import os
import re
from setuptools import setup, find_packages


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
VERSION_RE = re.compile(r"__version__\s+=\s+(.*)")


def read(*path):
    full_path = os.path.join(PROJECT_ROOT, *path)
    with codecs.open(full_path, "r", encoding="utf-8") as f:
        return f.read()


version_string = VERSION_RE.search(read("whitenoise/__init__.py")).group(1)
version = str(ast.literal_eval(version_string))


setup(
    name="whitenoise",
    version=version,
    author="David Evans",
    author_email="d@evans.io",
    url="http://whitenoise.evans.io",
    packages=find_packages(exclude=["tests*"]),
    license="MIT",
    description="Radically simplified static file serving for WSGI applications",
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    extras_require={"brotli": ["Brotli"]},
    python_requires=">=3.5, <4",
)
