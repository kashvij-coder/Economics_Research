# Economics Research

Generated Fashion Transparency Index score work.

## Files

- `fashion_company_financials.py`: contains the 250 transcribed brand scores and Yahoo Finance enrichment logic.
- `fashion_company_financials_output.csv`: generated enriched dataset.
- `fashion_company_financials_output.json`: generated enriched dataset in JSON format.

Run the script with Python 3.11+:

```bash
python fashion_company_financials.py
```

The Yahoo Finance enrichment leaves private or unresolved companies blank with a note rather than filling questionable ticker matches.
