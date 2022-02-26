# yfinance_snapshot
Takes regular snapshots of yfinance data for personal analysis purposes.
See https://github.com/ranaroussi/yfinance

## Motivations

* I found historical trends of many analysts, financial, and statistic data to be helpful for
  stock analysis. However, with existing APIs like yfinance, it's only possible to obtain
  limited historical values (e.g. 7/30/60/90 days ago).
* Yfinance has pretty high latency and the result lacks a schema, it's desired to cache the data
  and define a schema for easier usage.
* Practice my skills on open source tech stack: bazel + python + protobuf + docker + k8s

## Execution

* To deploy with docker:

  ```shell
  mkdir -p $HOME/yf_db/
  docker run -d --restart=unless-stopped \
      -e YF_SNAPSHOT_TICKERS="AAPL,MSFT,AMZN,FB,GOOG" \
      -e YF_SNAPSHOT_DB_PATH=/yf_db/ \
      -e YF_SNAPSHOT_ONESHOT=FALSE
      -v $HOME/yf_db/:/yf_db/ \
      wzong/yfinance-snapshot:latest
  ```

* For dev:

  ```shell
  mkdir -p /tmp/yf_testdb/
  export YF_SNAPSHOT_TICKERS="AAPL,MSFT,AMZN,FB,GOOG"
  export YF_SNAPSHOT_DB_PATH=/tmp/yf_testdb/
  bazel run runner:snapshot
  ```
