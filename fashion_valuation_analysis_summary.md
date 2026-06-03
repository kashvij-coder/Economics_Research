# Fashion Transparency Valuation Analysis

This analysis tests whether higher Fashion Transparency Index scores are associated with higher valuation multiples among public companies in the dataset.

The dataset is brand-level, but valuations are often parent-company-level. The ticker-level view dedupes repeated brands under the same public ticker and is the cleaner comparison.

## Sample

- Public brand rows with valuation data: 104
- Unique public tickers with valuation data: 77

## Correlation Results

Values are correlations between score and the log of the valuation multiple. The slope column approximates the percent change in the multiple associated with a 10-point higher score.

### Brand Rows

| Metric | N | Pearson | Spearman | Approx. p-value | R-squared | Slope per 10 score pts |
|---|---:|---:|---:|---:|---:|---:|
| MCap / revenue | 104 | 0.13 | 0.15 | 0.193 | 0.017 | 7.0% |
| EV / revenue | 104 | 0.18 | 0.20 | 0.064 | 0.033 | 8.2% |
| EV / EBITDA | 101 | 0.13 | 0.12 | 0.205 | 0.016 | 4.0% |

### Unique Tickers

| Metric | N | Pearson | Spearman | Approx. p-value | R-squared | Slope per 10 score pts |
|---|---:|---:|---:|---:|---:|---:|
| MCap / revenue | 77 | 0.07 | 0.07 | 0.536 | 0.005 | 4.4% |
| EV / revenue | 77 | 0.12 | 0.11 | 0.297 | 0.015 | 6.1% |
| EV / EBITDA | 75 | 0.11 | 0.07 | 0.348 | 0.012 | 4.1% |

## Score Quartiles, Unique Ticker View

- Low-score group: score <= 16.0, n = 20
- High-score group: score >= 48.0, n = 20

| Group | Median MCap / revenue | Median EV / revenue | Median EV / EBITDA |
|---|---:|---:|---:|
| Low score | 1.21 | 1.35 | 10.25 |
| High score | 1.24 | 1.52 | 14.47 |

## Regional Differences, Unique Ticker View

Region is inferred from ticker suffix and currency, so this is listing geography rather than a definitive headquarters or sales-exposure geography.

| Region | Tickers | Median Score | Median MCap / Revenue | Median EV / Revenue | Median EV / EBITDA | Score vs EV / Revenue Corr. |
|---|---:|---:|---:|---:|---:|---:|
| US-listed | 36 | 23.25 | 1.02 | 1.30 | 13.68 | 0.26 |
| Europe ex-UK | 15 | 40.00 | 1.24 | 1.95 | 11.88 | -0.19 |
| UK | 9 | 38.00 | 0.41 | 0.64 | 9.67 | -0.34 |
| China/HK | 5 | 0.00 | 1.90 | 1.98 | 9.56 | 0.89 |
| Japan | 5 | 18.00 | 1.02 | 1.08 | 9.71 | 0.94 |
| Australia/NZ | 4 | 34.00 | 0.33 | 0.64 | 12.39 | 0.97 |
| Canada | 1 | 22.00 | 4.97 | 5.27 | 24.67 |  |
| Latin America | 1 | 11.00 | 1.03 | 1.21 | 4.76 |  |
| Other/EUR | 1 | 33.00 | 1.74 | 2.25 | 9.81 |  |

## Interpretation

The full public-company sample shows only a weak positive relationship between transparency score and valuation multiples. In the cleaner unique-ticker view, the relationship becomes very small: score versus EV / revenue has a correlation around 0.12 and explains roughly 1.5% of variation in log EV / revenue.

Geography matters more for score distribution than for a clear valuation effect. Europe ex-UK and the UK have higher median transparency scores than the US-listed group, but the UK has lower valuation multiples, suggesting sector mix, luxury exposure, growth expectations, margins, and parent-company business mix are likely stronger drivers.

This is association, not causation. The next improvement would add explicit headquarters/listing country, industry category, growth, margin, and luxury-versus-retail controls.
