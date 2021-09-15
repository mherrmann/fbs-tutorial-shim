from fbs_tutorial_shim import pack, unpack, UnknownHash
from os import makedirs, chdir, getcwd, listdir
from os.path import dirname, isdir, join, abspath
from tempfile import TemporaryDirectory
from unittest import TestCase

class PackUnpackTest(TestCase):
	def test_pack_unpack(self):
		self.write_to_file('main.py', '1')
		self.write_to_file('src/constant.txt', 'constant')
		self.write_to_file('src/changing.txt', 'v1')
		pack('main.py', 'src', 'packed')
		unpack('main.py', 'packed', 'unpacked_1')
		self.assert_dirs_are_equal('src', 'unpacked_1')

		self.write_to_file('main.py', '2')
		self.write_to_file('src/changing.txt', 'v2')
		pack('main.py', 'src', 'packed')
		unpack('main.py', 'packed', 'unpacked_2')
		self.assert_dirs_are_equal('src', 'unpacked_2')

		self.write_to_file('main.py', '3')
		with self.assertRaises(UnknownHash):
			unpack('main.py', 'packed', 'unpacked_3')
	def setUp(self):
		super().setUp()
		self.tmp_dir = TemporaryDirectory()
		self.cwd_before = getcwd()
		chdir(self.tmp_dir.name)
	def tearDown(self):
		chdir(self.cwd_before)
		self.tmp_dir.cleanup()
		super().tearDown()
	def write_to_file(self, path, contents):
		makedirs(dirname(abspath(path)), exist_ok=True)
		with open(path, 'w') as f:
			f.write(contents)
	def assert_dirs_are_equal(self, expected, actual):
		self.assertEqual(
			_get_dir_contents_as_dict(expected),
			_get_dir_contents_as_dict(actual)
		)

def _get_dir_contents_as_dict(dir_path):
	result = {}
	for f in listdir(dir_path):
		f_path = join(dir_path, f)
		if isdir(f_path):
			result[f] = _get_dir_contents_as_dict(f_path)
		else:
			with open(f_path, 'rb') as f_handle:
				result[f] = f_handle.read()
	return result