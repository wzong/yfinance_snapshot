import datetime
import math
from typing import Any, Dict, Iterable

import pandas as pd
import yfinance as yf

from protos import yfinance_pb2 as yfpb

_REQUIRED_ANALYSIS = [
  'Growth',
  'End Date',
  'Earnings Estimate Avg',
  'Revenue Estimate Avg',
  'Earnings Estimate Growth',
]

def GetFloat(d: Dict[str, Any], key: str):
  if key in d:
    val = d[key]
  else:
    return None
  return float(val) if isinstance(val, int) or isinstance(val, float) else None

def GetInt(d: Dict[str, Any], key: str):
  if key in d:
    val = d[key]
  else:
    return None
  if isinstance(val, int) or isinstance(val, float):
    return int(val) if not math.isnan(val) else None

class YFinanceClient(object):

  def __init__(self, ticker: str):
    self.ticker = yf.Ticker(ticker)

  def GetAnalysis(self) -> yfpb.Analysis:
    data: pd.DataFrame = self.ticker.analysis
    result = yfpb.Analysis()

    if not self._CheckColumns(_REQUIRED_ANALYSIS, data.columns):
      return None

    for k, v in data.iterrows():
      p = yfpb.Period()
      p.name = k
      val = v['End Date']
      val = val.to_pydatetime() if val and val != pd.NaT else None
      val = val.strftime('%Y-%m-%d') if not pd.isnull(val) else None
      if val: p.end_date = val

      # EPS estimate
      val = GetFloat(v, 'Earnings Estimate Low')
      if val: p.eps_estimate.low = val

      val = GetFloat(v, 'Earnings Estimate High')
      if val: p.eps_estimate.high = val

      val = GetFloat(v, 'Earnings Estimate Avg')
      if val: p.eps_estimate.average = val

      val = GetFloat(v, 'Growth')  if k == '+5y' else GetFloat(v, 'Earnings Estimate Growth')
      if val: p.eps_estimate.growth = val

      val = GetInt(v, 'Earnings Estimate Number Of Analysts')
      if val: p.eps_estimate.num_analysts = val

      val = GetFloat(v, 'Earnings Estimate Year Ago Eps')
      if val: p.eps_estimate.year_ago = val

      # Revenue estimate
      val = GetFloat(v, 'Revenue Estimate Low')
      if val: p.revenue_estimate.low = val

      val = GetFloat(v, 'Revenue Estimate High')
      if val: p.revenue_estimate.high = val

      val = GetFloat(v, 'Revenue Estimate Avg')
      if val: p.revenue_estimate.average = val

      val = GetFloat(v, 'Growth') if k == '+5y' else GetFloat(v, 'Revenue Estimate Growth')
      if val: p.revenue_estimate.growth = val

      val = GetInt(v, 'Revenue Estimate Number Of Analysts')
      if val: p.revenue_estimate.num_analysts = val

      val = GetFloat(v, 'Revenue Estimate Year Ago Revenue')
      if val: p.revenue_estimate.year_ago = val

      # EPS snapshot
      for d in [7, 30, 60, 90]:
        s = yfpb.Snapshot()
        s.days_ago = d

        val = GetFloat(v, 'Eps Trend %dDays Ago' % d)
        if val: s.value = val

        val = GetInt(v, 'Eps Revisions Up Last%dDays' % d)
        if val: s.num_ups = val

        val = GetInt(v, 'Eps Revisions Down Last%dDays' % d)
        if val: s.num_downs = val

        p.eps_estimate_snapshots.append(s)

      result.periods.append(p)
    return result

  def GetInfo(self) -> yfpb.Info:
    data = self.ticker.info
    result = yfpb.Info()

    # Price target
    val  = GetFloat(data, 'targetLowPrice')
    if val: result.price_target.low = val

    val  = GetFloat(data, 'targetHighPrice')
    if val: result.price_target.high = val

    val  = GetFloat(data, 'targetMeanPrice')
    if val: result.price_target.average = val

    val  = GetInt(data, 'numberOfAnalystOpinions')
    if val: result.price_target.num_analysts = val

    # Profitability
    val  = GetFloat(data, 'profitMargins')
    if val: result.profitability.profit_margin = val

    val  = GetFloat(data, 'operatingMargins')
    if val: result.profitability.operating_margin = val

    val  = GetFloat(data, 'grossMargins')
    if val: result.profitability.gross_margin = val

    val  = GetFloat(data, 'ebitdaMargins')
    if val: result.profitability.ebitda_margin = val

    # Income statement
    val  = GetFloat(data, 'totalRevenue')
    if val: result.income.revenue = val

    val  = GetFloat(data, 'revenuePerShare')
    if val: result.income.revenue_per_share = val

    val  = GetFloat(data, 'revenueGrowth')
    if val: result.income.revenue_growth = val

    val  = GetFloat(data, 'revenueQuarterlyGrowth')
    if val: result.income.revenue_quarterly_growth = val

    val  = GetFloat(data, 'grossProfits')
    if val: result.income.gross_profit = val

    val  = GetFloat(data, 'ebitda')
    if val: result.income.ebitda = val

    val  = GetFloat(data, 'netIncomeToCommon')
    if val: result.income.earnings = val

    val  = GetFloat(data, 'trailingEps')
    if val: result.income.earnings_per_share = val

    val  = GetFloat(data, 'earningsGrowth')
    if val: result.income.earnings_growth = val

    val  = GetFloat(data, 'earningsQuarterlyGrowth')
    if val: result.income.earnings_quarterly_growth = val

    # Balance sheet
    val  = GetFloat(data, 'totalCash')
    if val: result.balance_sheet.total_cash = val

    val  = GetFloat(data, 'totalCashPerShare')
    if val: result.balance_sheet.total_cash_per_share = val

    val  = GetFloat(data, 'totalDebt')
    if val: result.balance_sheet.total_debt = val

    val  = GetFloat(data, 'debtToEquity')
    if val: result.balance_sheet.total_debt_to_equity = val

    val  = GetFloat(data, 'currentRatio')
    if val: result.balance_sheet.current_ratio = val

    val  = GetFloat(data, 'bookValue')
    if val: result.balance_sheet.book_value = val

    # Price history
    val  = GetFloat(data, 'beta')
    if val: result.price_history.beta = val

    val  = GetFloat(data, 'fiftyTwoWeekHigh')
    if val: result.price_history.high_52w = val

    val  = GetFloat(data, 'fiftyTwoWeekLow')
    if val: result.price_history.low_52w = val

    val  = GetFloat(data, 'fiftyDayAverage')
    if val: result.price_history.ma_50d = val

    val  = GetFloat(data, 'twoHundredDayAverage')
    if val: result.price_history.ma_200d = val

    # Share stats
    val  = GetFloat(data, 'averageVolume')
    if val: result.shares_stats.average_volume_3m = val

    val  = GetFloat(data, 'averageDailyVolume10Day')
    if val: result.shares_stats.average_volume_10d = val

    val  = GetFloat(data, 'sharesOutstanding')
    if val: result.shares_stats.outstanding = val

    val  = GetFloat(data, 'impliedSharesOutstanding')
    if val: result.shares_stats.implied_outstanding = val

    val  = GetFloat(data, 'floatShares')
    if val: result.shares_stats.float = val

    val  = GetFloat(data, 'heldPercentInsiders')
    if val: result.shares_stats.insider_precent = val

    val  = GetFloat(data, 'heldPercentInstitutions')
    if val: result.shares_stats.institutions_percent = val

    val  = GetFloat(data, 'sharesShort')
    if val: result.shares_stats.short = val

    val  = GetFloat(data, 'sharesShortPriorMonth')
    if val: result.shares_stats.short_prev_month = val

    val  = GetFloat(data, 'shortRatio')
    if val: result.shares_stats.short_ratio = val

    # Dividend
    val  = GetFloat(data, 'dividendRate')
    if val: result.dividend.forward = val

    val  = GetFloat(data, 'dividendYield')
    if val: result.dividend.forward_yield = val

    val  = GetFloat(data, 'exDividendDate')
    if val: result.dividend.ex_date = datetime.datetime.fromtimestamp(val).strftime('%Y-%m-%d')

    val  = GetFloat(data, 'payoutRatio')
    if val: result.dividend.payout_ratio = val

    val  = GetFloat(data, 'trailingAnnualDividendRate')
    if val: result.dividend.trailing = val

    val  = GetFloat(data, 'trailingAnnualDividendYield')
    if val: result.dividend.trailing_yield = val

    val  = GetFloat(data, 'fiveYearAvgDividendYield')
    if val: result.dividend.trailing_yield_5y = val

    return result

  def _CheckColumns(self, required: Iterable[str], columns: Iterable[str]):
    missing = []
    for k in required:
      if k not in columns:
        missing.append(k)
    if missing:
      print('Missing required keys: %s' % missing)
      return False
    return True
