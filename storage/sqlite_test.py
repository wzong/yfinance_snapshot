import os
import shutil
import tempfile
import unittest

from storage import sqlite

_DATE1 = '2022-01-01'
_DATE2 = '2022-01-02'
_DATE3 = '2022-01-03'

class TestSqliteStorage(unittest.TestCase):

  def setUp(self) -> None:
    self.tmp_dir = tempfile.mkdtemp()
    self.storage = sqlite.SqliteStorage(self.tmp_dir)
    self.storage.Reset()

  def tearDown(self) -> None:
    shutil.rmtree(self.tmp_dir)

  def testList(self):
    self.storage.Write('T1', _DATE1, 'd1'.encode('utf-8'), 'grp')
    self.storage.Write('T2', _DATE1, 'd2'.encode('utf-8'), 'grp')
    self.storage.Write('T2', _DATE2, 'd3'.encode('utf-8'), 'grp')
    self.assertEqual(self.storage.List('grp'),  {
      'T1': [_DATE1],
      'T2': [_DATE1, _DATE2],
    })

  def testReadWrite(self):
    self.storage.Write('T', _DATE1, 'd1'.encode('utf-8'), 'grp')
    self.assertEqual(
      self.storage.Read('T', _DATE1, 'grp'), 'd1'.encode('utf-8'))


  def testReadLatest(self):
    self.storage.Write('T', _DATE2, 'd2'.encode('utf-8'), 'grp')
    self.storage.Write('T', _DATE3, 'd3'.encode('utf-8'), 'grp')
    self.storage.Write('T', _DATE1, 'd1'.encode('utf-8'), 'grp')
    self.assertEqual(
      self.storage.ReadLatest('T', 'grp'), 'd3'.encode('utf-8'))

  def testGetSet(self):
    self.storage.Set('key1', 'val1')
    self.assertEqual(self.storage.Get('key1'), 'val1')

  def testGetNonExist(self):
    self.assertIsNone(self.storage.Get('nonexist'))


class TestShardedSqliteStorage(unittest.TestCase):

  def setUp(self) -> None:
    self.tmp_dir = tempfile.mkdtemp()
    self.storage = sqlite.ShardedSqliteStorage(self.tmp_dir)
    self._Write('2020-02-01')
    self._Write('2021-01-01')
    self._Write('2021-02-01')
    self._Write('2021-12-01')

  def tearDown(self) -> None:
    shutil.rmtree(self.tmp_dir)

  def _Write(self, date_str: str):
    self.storage.Write('T', date_str, date_str.encode('utf-8'))

  def testGetQuarters(self):
    self.assertEqual(
      sqlite.GetQuarters(sqlite.GetDate('2021-05-31'), sqlite.GetDate('2022-01-31')),
      ['2021q2', '2021q3', '2021q4', '2022q1'])

  def testList(self):
    self.assertEqual(
      self.storage.List(date_gte='2020-01-01'),
      {'T': ['2020-02-01', '2021-01-01', '2021-02-01', '2021-12-01']})

  def testReadLatest(self):
    date = sqlite.GetDaysAgoStr(12)
    self._Write(date)
    self.assertEqual(self.storage.ReadLatest('T'), date.encode('utf-8'))

  def testGetSet(self):
    self.storage.Set('key1', 'val1'.encode('utf-8'))
    self.assertEqual(self.storage.Get('key1'), 'val1'.encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
