"""
This module contains a very trimmed-down version of fbs's built-in commands.
"""
from fbs import path, SETTINGS
from fbs.builtin_commands._util import prompt_for_value, \
    require_existing_project, require_frozen_app
from fbs.cmdline import command
from fbs.resources import copy_with_filtering
from fbs_runtime import FbsError
from fbs_runtime.platform import is_windows, is_mac, is_linux, is_arch_linux, \
    is_ubuntu, is_fedora
from fbs_tutorial_shim import unpack, UnknownHash
from os import listdir, remove, unlink, mkdir
from os.path import join, isfile, isdir, islink, dirname, exists
from shutil import rmtree

import logging
import os
import subprocess
import sys

_LOG = logging.getLogger(__name__)

_FIXED_APP_NAME = 'MyFbsApp'
_FIXED_AUTHOR = 'Author'
_FIXED_MAC_BUNDLE_IDENTIFIER = 'com.author.myfbsapp'
_FIXED_PYTHON_BINDINGS = 'PyQt5'

@command
def startproject():
    """
    Start a new project in the current directory
    """
    if exists('src'):
        raise FbsError('The src/ directory already exists. Aborting.')
    mkdir('src')
    template_dir = join(dirname(__file__), 'project_template')
    template_path = lambda relpath: join(template_dir, *relpath.split('/'))
    # fbs prompts the user for several values such as the app name.
    # We use hard-coded values to be able to use pre-compiled binaries.
    copy_with_filtering(
        template_dir, '.', {
            'app_name': _FIXED_APP_NAME,
            'author': _FIXED_AUTHOR,
            'mac_bundle_identifier': _FIXED_MAC_BUNDLE_IDENTIFIER,
            'python_bindings': _FIXED_PYTHON_BINDINGS
        },
        files_to_filter=[
            template_path('src/build/settings/base.json'),
            template_path('src/build/settings/mac.json'),
            template_path('src/main/python/main.py')
        ]
    )
    print('')
    _LOG.info(
        "Created the src/ directory. You can now do:\n\n"
        "    fbs run"
    )

@command
def run():
    """
    Run your app from source
    """
    require_existing_project()
    env = dict(os.environ)
    pythonpath = path('src/main/python')
    old_pythonpath = env.get('PYTHONPATH', '')
    if old_pythonpath:
        pythonpath += os.pathsep + old_pythonpath
    env['PYTHONPATH'] = pythonpath
    subprocess.run([sys.executable, path(SETTINGS['main_module'])], env=env)

@command
def freeze():
    """
    Compile your code to a standalone executable
    """
    require_existing_project()
    app_name = SETTINGS['app_name']
    main_py = path('src/main/python/main.py')
    if is_mac():
        import fbs_tutorial_shim_mac as os_shim_module
        executable = 'target/%s.app/Contents/MacOS/%s' % (app_name, app_name)
    elif is_windows():
        import fbs_tutorial_shim_windows as os_shim_module
        executable = join('target', app_name, app_name) + '.exe'
    else:
        # It would be nice to support Linux as well. But our current approach of
        # hosting OS-specific frozen binaries on PyPI does not allow it. Here's
        # why: We obtain OS-specific binaries by declaring them as dependencies
        # in setup.py. For example:
        #     fbs-tutorial-shim-windows; sys_platform=='windows'
        # For Linux, we need different binaries depending on the distribution.
        # However, sys_platform only gives us "linux". This means that we would
        # need to package the binaries for all Linux distributions in one PyPI
        # package. But here comes the problem: PyPI has a maximum file size of
        # 60 MB. This is not enough to contain the files for multiple
        # distributions.
        raise FbsError(
            "This copy of fbs does not support Linux, sorry.\n"
            "Please use Python 3.5/3.6 and `pip install fbs PyQt5==5.9.2`.\n"
            "Or obtain fbs Pro from https://build-system.fman.io/pro."
        )
    data_dir = join(dirname(os_shim_module.__file__), 'data')
    try:
        unpack(main_py, data_dir, path('${freeze_dir}'))
    except UnknownHash:
        raise FbsError(
            "This copy of fbs only supports main.py as in the tutorial.\n"
            "Please use Python 3.5/3.6 and `pip install fbs PyQt5==5.9.2`.\n"
            "Or obtain fbs Pro from https://build-system.fman.io/pro."
        )
    _LOG.info(
        "Done. You can now run `%s`. If that doesn't work, see "
        "https://build-system.fman.io/troubleshooting.", executable
    )

@command
def installer():
    """
    Create an installer for your app
    """
    require_frozen_app()
    linux_distribution_not_supported_msg = \
        "Your Linux distribution is not supported, sorry. " \
        "You can run `fbs buildvm` followed by `fbs runvm` to start a Docker " \
        "VM of a supported distribution."
    try:
        installer_fname = SETTINGS['installer']
    except KeyError:
        if is_linux():
            raise FbsError(linux_distribution_not_supported_msg)
        raise
    out_file = join('target', installer_fname)
    msg_parts = ['Created %s.' % out_file]
    if is_windows():
        from fbs.installer.windows import create_installer_windows
        create_installer_windows()
    elif is_mac():
        from fbs.installer.mac import create_installer_mac
        create_installer_mac()
    elif is_linux():
        app_name = SETTINGS['app_name']
        if is_ubuntu():
            from fbs.installer.ubuntu import create_installer_ubuntu
            create_installer_ubuntu()
            install_cmd = 'sudo dpkg -i ' + out_file
            remove_cmd = 'sudo dpkg --purge ' + app_name
        elif is_arch_linux():
            from fbs.installer.arch import create_installer_arch
            create_installer_arch()
            install_cmd = 'sudo pacman -U ' + out_file
            remove_cmd = 'sudo pacman -R ' + app_name
        elif is_fedora():
            from fbs.installer.fedora import create_installer_fedora
            create_installer_fedora()
            install_cmd = 'sudo dnf install ' + out_file
            remove_cmd = 'sudo dnf remove ' + app_name
        else:
            raise FbsError(linux_distribution_not_supported_msg)
        msg_parts.append(
            'You can for instance install it via the following command:\n'
            '    %s\n'
            'This places it in /opt/%s. To uninstall it again, you can use:\n'
            '    %s'
            % (install_cmd, app_name, remove_cmd)
        )
    else:
        raise FbsError('Unsupported OS')
    _LOG.info(' '.join(msg_parts))

@command
def clean():
    """
    Remove previous build outputs
    """
    try:
        rmtree(path('target'))
    except FileNotFoundError:
        return
    except OSError:
        # In a docker container, target/ may be mounted so we can't delete it.
        # Delete its contents instead:
        for f in listdir(path('target')):
            fpath = join(path('target'), f)
            if isdir(fpath):
                rmtree(fpath, ignore_errors=True)
            elif isfile(fpath):
                remove(fpath)
            elif islink(fpath):
                unlink(fpath)

_REQUIRES_FULL_FBS_COPY = \
    "This copy of fbs only supports the tutorial commands, sorry.\n" \
    "Please use Python 3.5/3.6 and `pip install fbs PyQt5==5.9.2`.\n" \
    "Or obtain fbs Pro from https://build-system.fman.io/pro."

@command
def sign():
    """
    Sign your app, so the user's OS trusts it
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def sign_installer():
    """
    Sign installer, so the user's OS trusts it
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def repo():
    """
    Generate files for automatic updates
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def upload():
    """
    Upload installer and repository to fbs.sh
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def release(version=None):
    """
    Bump version and run clean,freeze,...,upload
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def test():
    """
    Execute your automated tests
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def buildvm():
    """
    Build a Linux VM. Eg.: buildvm ubuntu
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def runvm():
    """
    Run a Linux VM. Eg.: runvm ubuntu
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)

@command
def gengpgkey():
    """
    Generate a GPG key for Linux code signing
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)
@command
def register():
    """
    Create an account for uploading your files
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)
@command
def login():
    """
    Save your account details to secret.json
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)
@command
def init_licensing():
    """
    Generate public/private keys for licensing
    """
    raise FbsError(_REQUIRES_FULL_FBS_COPY)