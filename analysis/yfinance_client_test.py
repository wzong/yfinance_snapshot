from typing import Iterable
import unittest

from google.protobuf import message

from analysis import yfinance_client

def Trim(arr):
  return [x for x in arr if x]

class TestSqliteStorage(unittest.TestCase):

  def testTrim(self):
    self.assertFalse(Trim(['']))
    self.assertFalse(Trim([0.0]))
    self.assertFalse(Trim([0]))

  def testGetAnalysis(self):
    client = yfinance_client.YFinanceClient('AAPL')
    res = client.GetAnalysis()

    # Period names
    self.assertEqual(
      set([p.name for p in res.periods]),
      set(['-5Y', '0Q', '+1Q', '0Y', '+1Y', '+5Y']))

    # End Date
    self.assertTrue(Trim([p.end_date for p in res.periods]))

    # Eps estimate
    self.assertTrue(Trim([p.eps_estimate.low for p in res.periods]))
    self.assertTrue(Trim([p.eps_estimate.high for p in res.periods]))
    self.assertTrue(Trim([p.eps_estimate.average for p in res.periods]))
    self.assertTrue(Trim([p.eps_estimate.num_analysts for p in res.periods]))
    self.assertTrue(Trim([p.eps_estimate.growth for p in res.periods]))
    self.assertTrue(Trim([p.eps_estimate.year_ago for p in res.periods]))

    # Revenue estimate
    self.assertTrue(Trim([p.revenue_estimate.low for p in res.periods]))
    self.assertTrue(Trim([p.revenue_estimate.high for p in res.periods]))
    self.assertTrue(Trim([p.revenue_estimate.average for p in res.periods]))
    self.assertTrue(Trim([p.revenue_estimate.num_analysts for p in res.periods]))
    self.assertTrue(Trim([p.revenue_estimate.growth for p in res.periods]))
    self.assertTrue(Trim([p.revenue_estimate.year_ago for p in res.periods]))

    # EPS estimate snapshot
    for p in res.periods:
      self.assertEqual(
        set([s.days_ago for s in p.eps_estimate_snapshots]),
        set([7, 30, 60, 90]))

  def testGetInfo(self):
    client = yfinance_client.YFinanceClient('AAPL')
    res = client.GetInfo()
    self._AssertHasAllFields(res.price_target, ['growth', 'year_ago'])
    self._AssertHasAllFields(res.profitability)
    self._AssertHasAllFields(res.income, ['revenue_quarterly_growth', 'earnings_quarterly_growth'])
    self._AssertHasAllFields(res.balance_sheet)
    self._AssertHasAllFields(res.price_history)
    self._AssertHasAllFields(res.shares_stats, ['implied_outstanding'])
    self._AssertHasAllFields(res.dividend, ['date'])

  def _AssertHasAllFields(self, msg: message.Message, optional_fields: Iterable[str] = []):
    missing = []
    for descriptor in msg.DESCRIPTOR.fields:
      val = getattr(msg, descriptor.name)
      if descriptor.name not in optional_fields and val == descriptor.default_value:
        missing.append(descriptor.name)
    if missing:
      raise AssertionError('Field is not set: %s' % missing)

if __name__ == '__main__':
    unittest.main()
