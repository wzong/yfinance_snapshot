import datetime
import os
import json
import logging
import time
import traceback

from analysis import yfinance_client
from storage import sqlite

def TakeSnapshot(ticker, db: sqlite.ShardedSqliteStorage, db_raw: sqlite.ShardedSqliteStorage):
  date_str = datetime.datetime.now().strftime('%Y-%m-%d')
  client = yfinance_client.YFinanceClient(ticker)
  analysis = client.GetAnalysis()
  info = client.GetInfo()

  db.Write(ticker, date_str, analysis.SerializeToString(), group='yf.analysis')
  db.Write(ticker, date_str, info.SerializeToString(), group='yf.info')

  if db_raw:
    db_raw.Write(
      ticker, date_str, client.ticker.analysis.to_json().encode('utf-8'), group='yf.analysis')
    db_raw.Write(ticker, date_str, json.dumps(client.ticker.info).encode('utf-8'), group='yf.info')

def EnsureEnv(key: str):
  val = os.getenv(key)
  if not val:
    raise Exception('Environment var must be set: %s' % key)
  return val

if __name__ == '__main__':
  logging.basicConfig(
      format='%(asctime)s %(levelname)-8s %(message)s',
      level=logging.INFO,
      datefmt='%Y-%m-%d %H:%M:%S')
  logging.basicConfig(
      format='%(asctime)s %(levelname)-8s %(message)s',
      level=logging.ERROR,
      datefmt='%Y-%m-%d %H:%M:%S')

  # ONE-SHOT Mode
  oneshot_mode = os.getenv('YF_SNAPSHOT_ONESHOT', 'TRUE')

  # DB
  db_path = EnsureEnv('YF_SNAPSHOT_DB_PATH')
  db = sqlite.ShardedSqliteStorage(db_path)

  # DB (Raw Data)
  db_raw_path = os.getenv('YF_SNAPSHOT_DB_RAW_PATH', '')

  # Tickers (with cache)
  tickers_str = db.Get('YF_SNAPSHOT_TICKERS')
  if not tickers_str:
    tickers_str = EnsureEnv('YF_SNAPSHOT_TICKERS')
    db.Set('YF_SNAPSHOT_TICKERS', tickers_str)

  while True:
    db = sqlite.ShardedSqliteStorage(db_path)
    db_raw = sqlite.ShardedSqliteStorage(db_raw_path) if db_raw_path else None

    errors = []
    for t in tickers_str.split(','):
      t = t.strip()
      logging.info('Snapshotting %s' % t)
      try:
        TakeSnapshot(t, db, db_raw)
      except:
        errors.append(t)
        logging.error(traceback.format_exc())

    err_msg = 'Failed to snapshot: [%s]' % ','.join(errors)

    if oneshot_mode == 'FALSE':
      if errors:
        raise Exception(err_msg)
      else:
        logging.info('Finished oneshot')
      break
    else:
      if errors:
        logging.error(err_msg)
      logging.info('Sleeping for 7200s...')
      time.sleep(7200)
