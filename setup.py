from setuptools import setup, find_packages

import sys
import prep

if sys.version_info < (2, 7):
    install_requires = ['argparse']
else:
    install_requires = []

setup_args = dict(
    name             = 'prep',
    version          = prep.__version__,
    author           = 'Chris Petersen',
    author_email     = 'geek@ex-nerd.com',
    url              = 'https://github.com/ex-nerd/prep',
    license          = 'LICENSE.txt',
    description      = 'Pre-deployment config and template parser',
    long_description = open('README.rst').read(),
    install_requires = install_requires,
    py_modules       = ['prep'],
    entry_points     = {
        'console_scripts': [
            'prep = prep:prep',
        ],
    }
)

if __name__ == '__main__':
    setup(**setup_args)
