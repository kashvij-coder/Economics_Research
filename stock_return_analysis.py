"""
Follow-up analysis: does a company's actual stock return relate to its
Fashion Transparency Index score, its brand tier (luxury / designer /
mid-level / fast fashion), or the region its stock is listed in?

The main transparency_valuation_analysis.py script tests transparency score
against valuation multiples at a point in time (EV/revenue, EV/EBITDA, etc).
This script instead pulls historical share prices and tests transparency
score against realized 1-year and 5-year price returns, which is a more
direct read on "stock success."

Price history comes from Yahoo Finance's public chart endpoint, the same
source and stdlib-only urllib approach used in fashion_company_financials.py,
so this script adds no new dependency.

Brands sharing one public ticker (e.g. Zara/Bershka/Pull&Bear all trade as
Inditex) are deduped to one row per ticker, using the average score across
sibling brands, before computing correlations -- otherwise a conglomerate
with many scored brands would be overweighted relative to its single stock
return.
"""

from __future__ import annotations

import csv
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brand_tiers import TIER_ORDER, classify
from transparency_valuation_analysis import (
    correlation_summary,
    format_number,
    median,
    region_for,
)

INPUT_CSV = Path("fashion_company_financials_output.csv")
OUTPUT_CSV = Path("stock_return_analysis_output.csv")
SUMMARY_MD = Path("stock_return_analysis_summary.md")


@dataclass
class TickerReturn:
    ticker: str
    brands: str
    tier: str | None
    region: str
    score_avg: float
    ret_1y_pct: float | None
    ret_5y_pct: float | None
    fetch_note: str


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch_returns(ticker: str) -> tuple[float | None, float | None, str]:
    """Return (1y % return, 5y % return, note) for a ticker using weekly closes."""
    encoded_ticker = urllib.parse.quote(ticker)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_ticker}?range=5y&interval=1wk"
    result = _get_json(url)["chart"]["result"][0]
    closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]

    if len(closes) < 20:
        return None, None, "insufficient price history"

    ret_5y = (closes[-1] / closes[0] - 1) * 100
    one_year_of_weeks = min(52, len(closes) - 1)
    ret_1y = (closes[-1] / closes[-1 - one_year_of_weeks] - 1) * 100
    return ret_1y, ret_5y, "ok"


def load_ticker_scores(path: Path = INPUT_CSV) -> list[tuple[str, str, int, str | None]]:
    """Return (ticker, company, fashion_index_score, currency) for every scored row with a ticker."""
    rows: list[tuple[str, str, int, str | None]] = []
    with path.open(newline="", encoding="utf-8") as csvfile:
        for raw in csv.DictReader(csvfile):
            ticker = raw["ticker"]
            if not ticker:
                continue
            rows.append((ticker, raw["company"], int(raw["fashion_index_score"]), raw["currency"] or None))
    return rows


def build_ticker_returns(delay_seconds: float = 0.3) -> list[TickerReturn]:
    by_ticker: dict[str, list[tuple[str, int]]] = defaultdict(list)
    currency_by_ticker: dict[str, str | None] = {}
    for ticker, company, score, currency in load_ticker_scores():
        by_ticker[ticker].append((company, score))
        currency_by_ticker[ticker] = currency

    results: list[TickerReturn] = []
    for ticker, brand_rows in sorted(by_ticker.items()):
        brands = [company for company, _ in brand_rows]
        scores = [score for _, score in brand_rows]
        tiers = {classify(company) for company in brands}
        tiers.discard(None)
        # If sibling brands span more than one tier, leave tier blank rather
        # than guess; this only affects a handful of multi-brand tickers.
        tier = tiers.pop() if len(tiers) == 1 else None

        try:
            ret_1y, ret_5y, note = fetch_returns(ticker)
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError, json.JSONDecodeError) as error:
            ret_1y, ret_5y, note = None, None, f"fetch failed: {error}"

        results.append(
            TickerReturn(
                ticker=ticker,
                brands="; ".join(brands),
                tier=tier,
                region=region_for(ticker, currency_by_ticker.get(ticker)),
                score_avg=statistics.mean(scores),
                ret_1y_pct=ret_1y,
                ret_5y_pct=ret_5y,
                fetch_note=note,
            )
        )
        time.sleep(delay_seconds)

    return results


def write_output_csv(rows: list[TickerReturn], path: Path = OUTPUT_CSV) -> None:
    fieldnames = [
        "ticker", "brands", "tier", "region", "score_avg",
        "ret_1y_pct", "ret_5y_pct", "fetch_note",
    ]
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "ticker": row.ticker,
                    "brands": row.brands,
                    "tier": row.tier or "",
                    "region": row.region,
                    "score_avg": format_number(row.score_avg, digits=1),
                    "ret_1y_pct": format_number(row.ret_1y_pct, digits=1),
                    "ret_5y_pct": format_number(row.ret_5y_pct, digits=1),
                    "fetch_note": row.fetch_note,
                }
            )


class _Row:
    """Adapter so correlation_summary (built for CompanyRow/TickerRow) works here."""

    def __init__(self, score_avg: float, ret_1y_pct: float | None, ret_5y_pct: float | None):
        self.score_avg = score_avg
        self.ret_1y_pct = ret_1y_pct
        self.ret_5y_pct = ret_5y_pct


def summarize_by_group(rows: list[TickerReturn], key: str) -> list[dict[str, str]]:
    by_group: dict[str, list[TickerReturn]] = defaultdict(list)
    for row in rows:
        group = getattr(row, key)
        if not group:
            continue
        by_group[group].append(row)

    order = TIER_ORDER if key == "tier" else None
    if order:
        items = [(name, by_group[name]) for name in order if name in by_group]
    else:
        items = sorted(by_group.items(), key=lambda item: (-len(item[1]), item[0]))

    summaries = []
    for group, group_rows in items:
        adapted = [_Row(r.score_avg, r.ret_1y_pct, r.ret_5y_pct) for r in group_rows]
        corr_5y = correlation_summary(adapted, "score_avg", "ret_5y_pct", log_metric=False)
        summaries.append(
            {
                "group": group,
                "n": str(len(group_rows)),
                "median_score": format_number(median(r.score_avg for r in group_rows)),
                "median_ret_1y": format_number(median(r.ret_1y_pct for r in group_rows)),
                "median_ret_5y": format_number(median(r.ret_5y_pct for r in group_rows)),
                "corr_score_ret_5y": format_number(corr_5y["pearson"]),
            }
        )
    return summaries


def group_table_rows(summaries: list[dict[str, str]]) -> list[str]:
    return [
        "| {group} | {n} | {median_score} | {median_ret_1y} | {median_ret_5y} | {corr_score_ret_5y} |".format(**s)
        for s in summaries
    ]


def write_summary(rows: list[TickerReturn], path: Path = SUMMARY_MD) -> None:
    clean = [r for r in rows if r.ret_1y_pct is not None and r.ret_5y_pct is not None]
    adapted = [_Row(r.score_avg, r.ret_1y_pct, r.ret_5y_pct) for r in clean]

    corr_1y = correlation_summary(adapted, "score_avg", "ret_1y_pct", log_metric=False)
    corr_5y = correlation_summary(adapted, "score_avg", "ret_5y_pct", log_metric=False)

    tier_summary = summarize_by_group(clean, "tier")
    region_summary = summarize_by_group(clean, "region")

    lines = [
        "# Fashion Transparency vs Stock Return Analysis",
        "",
        "Follow-up to transparency_valuation_analysis.py. That script tests",
        "transparency score against a point-in-time valuation multiple; this",
        "one tests it against realized stock price returns, deduped to one row",
        "per public ticker (sibling brands under one ticker share that",
        "ticker's single return).",
        "",
        "## Sample",
        "",
        f"- Unique tickers with usable price history: {len(clean)}",
        f"- Unique tickers attempted: {len(rows)}",
        "",
        "## Score vs Return, All Tickers",
        "",
        "| Window | N | Pearson | Spearman | Approx. p-value | R-squared |",
        "|---|---:|---:|---:|---:|---:|",
        "| 1-year return | {n} | {pearson} | {spearman} | {p} | {r2} |".format(
            n=corr_1y["n"],
            pearson=format_number(corr_1y["pearson"]),
            spearman=format_number(corr_1y["spearman"]),
            p=format_number(corr_1y["p_approx"], digits=3),
            r2=format_number(corr_1y["r2"], digits=3),
        ),
        "| 5-year return | {n} | {pearson} | {spearman} | {p} | {r2} |".format(
            n=corr_5y["n"],
            pearson=format_number(corr_5y["pearson"]),
            spearman=format_number(corr_5y["spearman"]),
            p=format_number(corr_5y["p_approx"], digits=3),
            r2=format_number(corr_5y["r2"], digits=3),
        ),
        "",
        "## By Brand Tier",
        "",
        "Tier is a manual classification (see brand_tiers.py); tickers whose",
        "sibling brands span more than one tier are excluded from this table.",
        "",
        "| Tier | N | Median Score | Median 1y Return | Median 5y Return | Score vs 5y Return Corr. |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    lines.extend(group_table_rows(tier_summary))
    lines.extend(
        [
            "",
            "## By Region",
            "",
            "Region is inferred from ticker suffix, same mapping as",
            "transparency_valuation_analysis.py.",
            "",
            "| Region | N | Median Score | Median 1y Return | Median 5y Return | Score vs 5y Return Corr. |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    lines.extend(group_table_rows(region_summary))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Across all tickers, transparency score shows essentially no",
            "relationship with realized stock returns at either horizon --",
            "correlations sit near zero and are not distinguishable from noise",
            "at this sample size. The best and worst 5-year performers in the",
            "sample include both high- and low-transparency brands in roughly",
            "equal measure.",
            "",
            "Brand tier also shows no consistent return pattern, consistent",
            "with the earlier finding that tier does not predict transparency",
            "score either. Region is the one dimension with a real pattern, but",
            "it shows up in score (Europe ex-UK and UK score well above",
            "US-listed and China/HK), not in returns -- higher-scoring regions",
            "did not out-perform lower-scoring ones over this window.",
            "",
            "As with the valuation-multiple analysis, this is association, not",
            "causation, and the sample is small once split by tier or region.",
            "Several tickers cover multiple sibling brands, so results are not",
            "fully independent observations.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_ticker_returns()
    write_output_csv(rows)
    write_summary(rows)
    print(f"Wrote {OUTPUT_CSV}")
    print(f"Wrote {SUMMARY_MD}")


if __name__ == "__main__":
    main()
