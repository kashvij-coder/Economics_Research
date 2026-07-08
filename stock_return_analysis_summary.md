# Fashion Transparency vs Stock Return Analysis

Follow-up to transparency_valuation_analysis.py. That script tests
transparency score against a point-in-time valuation multiple; this
one tests it against realized stock price returns, deduped to one row
per public ticker (sibling brands under one ticker share that
ticker's single return).

## Sample

- Unique tickers with usable price history: 78
- Unique tickers attempted: 78

## Score vs Return, All Tickers

| Window | N | Pearson | Spearman | Approx. p-value | R-squared |
|---|---:|---:|---:|---:|---:|
| 1-year return | 78 | -0.10 | -0.06 | 0.409 | 0.009 |
| 5-year return | 78 | 0.08 | -0.01 | 0.469 | 0.007 |

## By Brand Tier

Tier is a manual classification (see brand_tiers.py); tickers whose
sibling brands span more than one tier are excluded from this table.

| Tier | N | Median Score | Median 1y Return | Median 5y Return | Score vs 5y Return Corr. |
|---|---:|---:|---:|---:|---:|
| Luxury | 9 | 29.00 | -0.60 | -25.20 | -0.72 |
| Designer | 4 | 22.00 | 31.56 | 34.34 | 0.44 |
| Mid-Level | 34 | 31.00 | 13.88 | -11.12 | -0.10 |
| Fast Fashion | 8 | 45.00 | 9.40 | -71.47 | 0.65 |

## By Region

Region is inferred from ticker suffix, same mapping as
transparency_valuation_analysis.py.

| Region | N | Median Score | Median 1y Return | Median 5y Return | Score vs 5y Return Corr. |
|---|---:|---:|---:|---:|---:|
| US-listed | 36 | 23.25 | 9.69 | -11.12 | -0.11 |
| Europe ex-UK | 16 | 41.50 | 8.83 | -21.01 | 0.30 |
| UK | 9 | 38.00 | 9.62 | -48.76 | 0.29 |
| China/HK | 5 | 0.00 | -8.44 | -47.06 | 0.21 |
| Japan | 5 | 18.00 | 27.85 | 227.94 | 0.64 |
| Australia/NZ | 4 | 34.00 | -10.26 | -39.02 | 0.92 |
| Canada | 1 | 22.00 | 92.64 | 299.78 |  |
| Latin America | 1 | 11.00 | 21.78 | 88.20 |  |
| Other/EUR | 1 | 33.00 | 48.00 | 11.25 |  |

## Interpretation

Across all tickers, transparency score shows essentially no
relationship with realized stock returns at either horizon --
correlations sit near zero and are not distinguishable from noise
at this sample size. The best and worst 5-year performers in the
sample include both high- and low-transparency brands in roughly
equal measure.

Brand tier also shows no consistent return pattern, consistent
with the earlier finding that tier does not predict transparency
score either. Region is the one dimension with a real pattern, but
it shows up in score (Europe ex-UK and UK score well above
US-listed and China/HK), not in returns -- higher-scoring regions
did not out-perform lower-scoring ones over this window.

As with the valuation-multiple analysis, this is association, not
causation, and the sample is small once split by tier or region.
Several tickers cover multiple sibling brands, so results are not
fully independent observations.
