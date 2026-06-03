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

Run the script with Python 3.11+:

```bash
python fashion_company_financials.py
```

The Yahoo Finance enrichment leaves private or unresolved companies blank with a note rather than filling questionable ticker matches.

Analyze valuation multiples with:

```bash
python transparency_valuation_analysis.py
```
