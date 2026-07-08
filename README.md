# Economics Research

Generated Fashion Transparency Index score work.

## Files

- `fashion_company_financials.py`: contains the 250 transcribed brand scores and Yahoo Finance enrichment logic.
- `fashion_company_financials_output.csv`: generated enriched dataset.
- `fashion_company_financials_output.json`: generated enriched dataset in JSON format.
- `transparency_valuation_analysis.py`: analyzes whether Fashion Transparency Index scores relate to public-company valuation multiples.
- `fashion_valuation_analysis_summary.md`: generated valuation and geography summary.
- `fashion_valuation_region_summary.csv`: generated region-level valuation summary.
- `fashion_valuation_ticker_analysis.csv`: generated ticker-level valuation dataset.
- `brand_tiers.py`: manual luxury / designer / mid-level / fast-fashion classification for a subset of brands, used by `stock_return_analysis.py`.
- `stock_return_analysis.py`: follow-up analysis testing Fashion Transparency Index score against realized 1-year and 5-year stock returns, broken out by brand tier and by region.
- `stock_return_analysis_summary.md`: generated returns, tier, and region summary.
- `stock_return_analysis_output.csv`: generated ticker-level dataset with returns, tier, and region.

Run the script with Python 3.11+:

```bash
python fashion_company_financials.py
```

The Yahoo Finance enrichment leaves private or unresolved companies blank with a note rather than filling questionable ticker matches.

Analyze valuation multiples with:

```bash
python transparency_valuation_analysis.py
```

Analyze stock returns, brand tier, and region with:

```bash
python stock_return_analysis.py
```

This fetches weekly share-price history per ticker from Yahoo Finance (same stdlib-only approach as `fashion_company_financials.py`), so it needs network access and takes a couple of minutes to run.
