"""fbs tutorial helper

See:
https://github.com/mherrmann/fbs-tutorial-shim
"""

from os.path import relpath, join
from setuptools import setup, find_packages

import os

def _get_package_data(pkg_dir, data_subdir):
    result = []
    for dirpath, _, filenames in os.walk(join(pkg_dir, data_subdir)):
        for filename in filenames:
            filepath = join(dirpath, filename)
            result.append(relpath(filepath, pkg_dir))
    return result

description = 'fbs tutorial helper'
setup(
    name='fbs-tutorial-shim',
    version='0.9.9',
    description=description,
    long_description=
        description + '\n\nSee: https://github.com/mherrmann/fbs-tutorial-shim',
    author='Michael Herrmann',
    author_email='michael+removethisifyouarehuman@herrmann.io',
    url='https://github.com/mherrmann/fbs-tutorial-shim',
    packages=find_packages(exclude=('tests', 'tests.*')),
    package_data={
        'fbs': _get_package_data('fbs', '_defaults'),
        'fbs.builtin_commands':
            _get_package_data('fbs/builtin_commands', 'project_template')
    },
    install_requires=[
        'PyQt5',
        'fbs-tutorial-shim-windows; sys_platform=="win32"',
        'fbs-tutorial-shim-mac; sys_platform=="darwin"'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
    
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    
        'Operating System :: OS Independent',
    
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',

        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'console_scripts': ['fbs=fbs.__main__:_main']
    },
    license='GPLv3 or later',
    keywords='PyQt',
    platforms=['MacOS', 'Windows'],
    test_suite='tests'
)