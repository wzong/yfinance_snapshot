from concurrent.futures import ThreadPoolExecutor
import datetime
import logging
import os
from typing import Dict, List

import sqlite3

class SqliteStorage(object):
  def __init__(self, db_dir: str, db_name='data'):
    super().__init__()
    self.db_path = os.path.join(db_dir, '%s.sqlite' % db_name)
    logging.info('Connecting to DB: %s' % self.db_path)
    self.con = sqlite3.connect(self.db_path)
    self._InitTables()

  def _InitTables(self):
    cur = self.con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS data
    (date text, ticker text, grp text, data BLOB,
     UNIQUE(date,ticker,grp))
    ''')
    self.con.commit()

  def Reset(self):
    cur = self.con.cursor()
    cur.execute('DROP TABLE data')
    self.con.commit()
    self._InitTables()

  def Get(self, key: str) -> bytes:
    """Returns non-dated config/cache value for the given key."""
    return self.Read(key, '1970-01-01', 'system')

  def Set(self, key: str, val: bytes):
    """Sets non-dated config/cache value for the given key."""
    return self.Write(key, '1970-01-01', val, 'system')

  def List(self, group: str='analysis', date_gte: str='2022-01-01') -> Dict[str, List[str]]:
    """Returns list of available dates for each ticker."""
    data_dict = {}
    cur = self.con.cursor()
    for row in cur.execute(
        'SELECT ticker, date FROM data WHERE grp = ? AND date >= ? ORDER BY date ASC;',
        (group, date_gte)):
      data_dict.setdefault(row[0], []).append(row[1])
    return data_dict

  def Read(self, ticker: str, date_str: str, group='analysis') -> bytes:
    """Returns the json data for the given ticker and date."""
    cur = self.con.cursor()
    result = None
    for row in cur.execute(
        'SELECT data FROM data WHERE ticker = ? AND date = ? AND grp = ?;',
        (ticker, date_str, group)):
      result = row[0]
    return result

  def ReadLatest(self, ticker: str, group='analysis') -> bytes:
    cur = self.con.cursor()
    result = None
    for row in cur.execute(
        'SELECT data FROM data WHERE ticker = ? AND grp = ? ORDER BY date DESC LIMIT 1;',
        (ticker, group)):
      result = row[0]
    return result

  def Write(self, ticker: str, date_str: str, data: bytes, group='analysis'):
    cur = self.con.cursor()
    cur.execute(
        'INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?)',
        (date_str, ticker, group, data))
    self.con.commit()


def GetQuarters(date_begin: datetime.datetime, date_end: datetime.datetime) -> str:
    result = []
    for y in range(date_begin.year, date_end.year + 1):
      q_begin = int(date_begin.month / 4) + 1 if y == date_begin.year else 1
      q_end = int(date_end.month / 4) + 1 if y == date_end.year else 4
      for q in range(q_begin, q_end + 1):
        result.append('%dq%d' % (y, q))
    return result


def GetDate(date_str: str) -> datetime.datetime:
  return datetime.datetime.strptime(date_str, '%Y-%m-%d')


def GetDaysAgo(days_ago: int) -> datetime.datetime:
  return datetime.datetime.now() - datetime.timedelta(days=days_ago)


def GetDaysAgoStr(days_ago: int) -> str:
  return GetDaysAgo(days_ago).strftime('%Y-%m-%d')


class ShardedSqliteStorage(object):
  def __init__(self, db_dir: str):
    self.db_dir = db_dir
    self.system = SqliteStorage(self.db_dir, 'system')
    self.shards: Dict[str, SqliteStorage] = {}

  def Get(self, key: str) -> bytes:
    return self.system.Get(key)

  def Set(self, key: str, val: str) -> bytes:
    return self.system.Set(key, val)

  def List(self, group: str='analysis', date_gte: str='2022-01-01') -> Dict[str, List[str]]:
    quarters = GetQuarters(GetDate(date_gte), datetime.datetime.now())
    def DoList(q):
      return SqliteStorage(self.db_dir, 'shard-' + q).List(group, date_gte)
    with ThreadPoolExecutor(max_workers = len(quarters)) as executor:
      data = executor.map(DoList, quarters)
      result: Dict[str, List[str]] = {}
      for elem in data:
        for ticker, date_list in elem.items():
          res = result.setdefault(ticker, [])
          for d in date_list:
            res.append(d)
      return result

  def Read(self, ticker: str, date_str: str, group='analysis') -> bytes:
    d = GetDate(date_str)
    q = GetQuarters(d, d)[0]
    return SqliteStorage(self.db_dir, 'shard-' + q).Read(ticker, date_str, group)

  def ReadLatest(self, ticker: str, group='analysis') -> bytes:
    tickers = self.List(group, GetDaysAgoStr(30))
    if ticker not in tickers:
      return None
    latest_date = tickers[ticker][-1]
    return self.Read(ticker, latest_date, group)

  def Write(self, ticker: str, date_str: str, data: bytes, group='analysis'):
    d = GetDate(date_str)
    q = GetQuarters(d, d)[0]
    return SqliteStorage(self.db_dir, 'shard-' + q).Write(ticker, date_str, data, group)
