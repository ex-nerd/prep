from setuptools import setup

import os, sys, re

if sys.version_info < (2, 6):
    raise Exception("prep requires Python 2.6 or higher.")
if sys.version_info < (2, 7):
    install_requires = ['argparse', 'ordereddict']
else:
    install_requires = []

# Load the version by reading prep.py, so we don't run into
# dependency loops by importing it into setup.py
version = None
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "prep.py")) as file:
    for line in file:
        m = re.search(r'__version__\s*=\s*(.+?\n)', line)
        if m:
            version = eval(m.group(1))
            break

setup_args = dict(
    name             = 'prep',
    version          = version,
    author           = 'Chris Petersen',
    author_email     = 'geek@ex-nerd.com',
    url              = 'https://github.com/ex-nerd/prep',
    license          = 'Modified BSD',
    description      = 'Pre-deployment configuration parser/generator',
    long_description = open('README.rst').read(),
    install_requires = install_requires,
    py_modules       = ['prep'],
    entry_points     = {
        'console_scripts': [
            'prep = prep:prep',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
)

if __name__ == '__main__':
    setup(**setup_args)
