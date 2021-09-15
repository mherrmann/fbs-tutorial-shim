from argparse import ArgumentParser
from os import makedirs
from os.path import join, relpath, dirname, isdir
from shutil import copy

import hashlib
import os

_BASE_FILE_NAME = 'base'

class UnknownHash(Exception):
    pass

def pack(main_py, src_dir, dst_dir):
    """
    On the first call, copies `src_dir` into `dst_dir`/<hash>/ and creates
    `dst_dir`/base with contents <hash>, where <hash> is the hash of `main_py`.

    On the second call, assuming <hash> is different, copies only those files
    that are new or changed into `dst_dir`/<hash>/.

    The motivation is the following: We want to pack directories whose contents
    are largely the same. Eg.:

        1/
            MyApp/
        2/
            MyApp/

    99% of the files in 1/MyApp and 2/MyApp have the same contents.
    Unfortunately, Python's shutil.make_archive(...) produces an archive that is
    almost twice the size of what we get when we compress just one of the two.
    By skipping unchanged files, the present implementation achieves
    significantly better compression.
    """
    main_py_hash = get_py_file_hash(main_py)
    base_file = join(dst_dir, _BASE_FILE_NAME)
    try:
        with open(base_file) as f:
            base = f.read()
    except FileNotFoundError:
        base = main_py_hash
        makedirs(dirname(base_file), exist_ok=True)
        with open(base_file, 'w') as f:
            f.write(main_py_hash)
    for subdir, _, files in os.walk(src_dir):
        for file_name in files:
            file_path = join(subdir, file_name)
            file_rel_path = relpath(file_path, src_dir)
            base_copy = join(dst_dir, base, file_rel_path)
            with open(file_path, 'rb') as f2:
                try:
                    with open(base_copy, 'rb') as f:
                        is_equal = f.read() == f2.read()
                except FileNotFoundError:
                    is_equal = False
            if not is_equal:
                dst_path = join(dst_dir, main_py_hash, file_rel_path)
                makedirs(dirname(dst_path), exist_ok=True)
                copy(file_path, dst_path)

def unpack(main_py, src_dir, dst_dir):
    main_py_hash = get_py_file_hash(main_py)
    if not isdir(join(src_dir, main_py_hash)):
        raise UnknownHash()
    base_file = join(src_dir, _BASE_FILE_NAME)
    with open(base_file) as f:
        base = f.read()
    _copytree(join(src_dir, base), dst_dir)
    _copytree(join(src_dir, main_py_hash), dst_dir)

def get_py_file_hash(file_path):
    with open(file_path) as f:
        contents_no_newlines = ''.join(line.strip() for line in f)
    m = hashlib.sha1()
    m.update(contents_no_newlines.encode('utf-8'))
    return m.digest().hex()

def _copytree(src_dir, dst_dir):
    for subdir, _, files in os.walk(src_dir):
        for file_name in files:
            file_path = join(subdir, file_name)
            file_rel_path = relpath(file_path, src_dir)
            dst_path = join(dst_dir, file_rel_path)
            makedirs(dirname(dst_path), exist_ok=True)
            copy(file_path, dst_path)

if __name__ == '__main__':
    parser = ArgumentParser(description='Package files for an OS shim.')
    parser.add_argument('main', help='main.py script')
    parser.add_argument('src', help='source dir. Eg. .../target/ubuntu/MyApp')
    parser.add_argument(
        'dst', help='dest dir. Eg. .../fbs_tutorial_shim_ubuntu/data'
    )
    args = parser.parse_args()
    pack(args.main, args.src, args.dst)