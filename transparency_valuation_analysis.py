"""
Analyze whether Fashion Transparency Index scores relate to public-company
valuation multiples.

The input data is brand-level, while many public valuation fields are
parent-company-level. This script reports both brand-row results and a deduped
ticker-level view so repeated brands under the same ticker do not dominate the
analysis.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


INPUT_CSV = Path("fashion_company_financials_output.csv")
SUMMARY_MD = Path("fashion_valuation_analysis_summary.md")
REGION_CSV = Path("fashion_valuation_region_summary.csv")
TICKER_CSV = Path("fashion_valuation_ticker_analysis.csv")


@dataclass
class CompanyRow:
    company: str
    fashion_index_score: int
    ticker: str
    yahoo_name: str | None
    market_cap: float
    revenue: float
    ebitda: float | None
    debt: float
    currency: str | None
    region: str
    mcap_revenue: float
    ev_revenue: float
    ev_ebitda: float | None


@dataclass
class TickerRow:
    ticker: str
    yahoo_name: str | None
    brands: str
    brand_count: int
    score_avg: float
    score_min: int
    score_max: int
    market_cap: float
    revenue: float
    ebitda: float | None
    debt: float
    currency: str | None
    region: str
    mcap_revenue: float
    ev_revenue: float
    ev_ebitda: float | None


def as_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def median(values: Iterable[float | None]) -> float | None:
    clean = sorted(value for value in values if value is not None and not math.isnan(value))
    if not clean:
        return None
    return statistics.median(clean)


def percentile(values: Iterable[float], quantile: float) -> float:
    clean = sorted(values)
    if not clean:
        raise ValueError("percentile requires at least one value")

    position = (len(clean) - 1) * quantile
    low_index = math.floor(position)
    high_index = math.ceil(position)
    if low_index == high_index:
        return clean[low_index]

    low_weight = high_index - position
    high_weight = position - low_index
    return clean[low_index] * low_weight + clean[high_index] * high_weight


def rank_values(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0

    while index < len(indexed):
        next_index = index + 1
        while next_index < len(indexed) and indexed[next_index][1] == indexed[index][1]:
            next_index += 1

        average_rank = (index + 1 + next_index) / 2
        for rank_index in range(index, next_index):
            ranks[indexed[rank_index][0]] = average_rank
        index = next_index

    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None

    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    sum_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    sum_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if sum_x == 0 or sum_y == 0:
        return None

    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / (sum_x * sum_y)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    return pearson(rank_values(xs), rank_values(ys))


def normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def correlation_summary(
    rows: Iterable[CompanyRow | TickerRow],
    score_attr: str,
    metric_attr: str,
    log_metric: bool = True,
) -> dict[str, float | int | None]:
    xs: list[float] = []
    ys: list[float] = []

    for row in rows:
        score = getattr(row, score_attr)
        metric = getattr(row, metric_attr)
        if score is None or metric is None:
            continue
        if log_metric:
            if metric <= 0:
                continue
            metric = math.log(metric)
        xs.append(float(score))
        ys.append(float(metric))

    if len(xs) < 3:
        return {
            "n": len(xs),
            "pearson": None,
            "spearman": None,
            "p_approx": None,
            "r2": None,
            "slope_per_10_score_pct": None,
        }

    corr = pearson(xs, ys)
    rho = spearman(xs, ys)
    if corr is None:
        p_approx = None
        r2 = None
    else:
        z_value = 0.5 * math.log((1 + corr) / (1 - corr)) * math.sqrt(len(xs) - 3)
        p_approx = 2 * (1 - normal_cdf(abs(z_value)))
        r2 = corr * corr

    slope_pct = slope_per_10_score_pct(xs, ys)
    return {
        "n": len(xs),
        "pearson": corr,
        "spearman": rho,
        "p_approx": p_approx,
        "r2": r2,
        "slope_per_10_score_pct": slope_pct,
    }


def slope_per_10_score_pct(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None

    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    sum_xx = sum((x - mean_x) ** 2 for x in xs)
    if sum_xx == 0:
        return None

    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / sum_xx
    return (math.exp(10 * slope) - 1) * 100


def region_for(ticker: str, currency: str | None) -> str:
    suffix = ticker.rsplit(".", 1)[-1] if "." in ticker else ""
    suffix_to_region = {
        "L": "UK",
        "PA": "Europe ex-UK",
        "MI": "Europe ex-UK",
        "DE": "Europe ex-UK",
        "SW": "Europe ex-UK",
        "MC": "Europe ex-UK",
        "ST": "Europe ex-UK",
        "HK": "China/HK",
        "SZ": "China/HK",
        "T": "Japan",
        "AX": "Australia/NZ",
        "NZ": "Australia/NZ",
        "TO": "Canada",
        "SN": "Latin America",
    }
    if suffix in suffix_to_region:
        return suffix_to_region[suffix]
    if not suffix and currency == "USD":
        return "US-listed"
    return f"Other/{currency or 'unknown'}"


def load_public_rows(path: Path = INPUT_CSV) -> list[CompanyRow]:
    rows: list[CompanyRow] = []
    with path.open(newline="", encoding="utf-8") as csvfile:
        for raw in csv.DictReader(csvfile):
            ticker = raw["ticker"]
            market_cap = as_float(raw["market_cap"])
            revenue = as_float(raw["revenue"])
            if not ticker or market_cap is None or revenue is None or revenue <= 0:
                continue

            ebitda = as_float(raw["ebitda"])
            debt = as_float(raw["debt"]) or 0.0
            ev = market_cap + debt
            currency = raw["currency"] or None
            rows.append(
                CompanyRow(
                    company=raw["company"],
                    fashion_index_score=int(raw["fashion_index_score"]),
                    ticker=ticker,
                    yahoo_name=raw["yahoo_name"] or None,
                    market_cap=market_cap,
                    revenue=revenue,
                    ebitda=ebitda,
                    debt=debt,
                    currency=currency,
                    region=region_for(ticker, currency),
                    mcap_revenue=market_cap / revenue,
                    ev_revenue=ev / revenue,
                    ev_ebitda=ev / ebitda if ebitda and ebitda > 0 else None,
                )
            )
    return rows


def dedupe_by_ticker(rows: list[CompanyRow]) -> list[TickerRow]:
    by_ticker: dict[str, list[CompanyRow]] = defaultdict(list)
    for row in rows:
        by_ticker[row.ticker].append(row)

    ticker_rows: list[TickerRow] = []
    for ticker, ticker_group in sorted(by_ticker.items()):
        base = ticker_group[0]
        scores = [row.fashion_index_score for row in ticker_group]
        ticker_rows.append(
            TickerRow(
                ticker=ticker,
                yahoo_name=base.yahoo_name,
                brands="; ".join(row.company for row in ticker_group),
                brand_count=len(ticker_group),
                score_avg=statistics.mean(scores),
                score_min=min(scores),
                score_max=max(scores),
                market_cap=base.market_cap,
                revenue=base.revenue,
                ebitda=base.ebitda,
                debt=base.debt,
                currency=base.currency,
                region=base.region,
                mcap_revenue=base.mcap_revenue,
                ev_revenue=base.ev_revenue,
                ev_ebitda=base.ev_ebitda,
            )
        )
    return ticker_rows


def summarize_by_region(rows: list[TickerRow]) -> list[dict[str, str]]:
    by_region: dict[str, list[TickerRow]] = defaultdict(list)
    for row in rows:
        by_region[row.region].append(row)

    summaries: list[dict[str, str]] = []
    for region, region_rows in sorted(by_region.items(), key=lambda item: (-len(item[1]), item[0])):
        corr = correlation_summary(region_rows, "score_avg", "ev_revenue")
        summaries.append(
            {
                "region": region,
                "unique_tickers": str(len(region_rows)),
                "median_score": format_number(median(row.score_avg for row in region_rows)),
                "median_mcap_revenue": format_number(median(row.mcap_revenue for row in region_rows)),
                "median_ev_revenue": format_number(median(row.ev_revenue for row in region_rows)),
                "median_ev_ebitda": format_number(median(row.ev_ebitda for row in region_rows)),
                "corr_score_log_ev_revenue": format_number(corr["pearson"]),
            }
        )
    return summaries


def format_number(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def write_ticker_csv(rows: list[TickerRow], path: Path = TICKER_CSV) -> None:
    fieldnames = [
        "ticker",
        "region",
        "currency",
        "brands",
        "brand_count",
        "score_avg",
        "score_min",
        "score_max",
        "market_cap",
        "revenue",
        "ebitda",
        "debt",
        "mcap_revenue",
        "ev_revenue",
        "ev_ebitda",
    ]
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: getattr(row, field) for field in fieldnames})


def write_region_csv(region_rows: list[dict[str, str]], path: Path = REGION_CSV) -> None:
    fieldnames = [
        "region",
        "unique_tickers",
        "median_score",
        "median_mcap_revenue",
        "median_ev_revenue",
        "median_ev_ebitda",
        "corr_score_log_ev_revenue",
    ]
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(region_rows)


def write_summary(rows: list[CompanyRow], ticker_rows: list[TickerRow], path: Path = SUMMARY_MD) -> None:
    row_level = {
        "MCap / revenue": correlation_summary(rows, "fashion_index_score", "mcap_revenue"),
        "EV / revenue": correlation_summary(rows, "fashion_index_score", "ev_revenue"),
        "EV / EBITDA": correlation_summary(rows, "fashion_index_score", "ev_ebitda"),
    }
    ticker_level = {
        "MCap / revenue": correlation_summary(ticker_rows, "score_avg", "mcap_revenue"),
        "EV / revenue": correlation_summary(ticker_rows, "score_avg", "ev_revenue"),
        "EV / EBITDA": correlation_summary(ticker_rows, "score_avg", "ev_ebitda"),
    }
    region_rows = summarize_by_region(ticker_rows)

    scores = [row.score_avg for row in ticker_rows]
    first_quartile = percentile(scores, 0.25)
    third_quartile = percentile(scores, 0.75)
    low_score = [row for row in ticker_rows if row.score_avg <= first_quartile]
    high_score = [row for row in ticker_rows if row.score_avg >= third_quartile]

    lines = [
        "# Fashion Transparency Valuation Analysis",
        "",
        "This analysis tests whether higher Fashion Transparency Index scores are associated with higher valuation multiples among public companies in the dataset.",
        "",
        "The dataset is brand-level, but valuations are often parent-company-level. The ticker-level view dedupes repeated brands under the same public ticker and is the cleaner comparison.",
        "",
        "## Sample",
        "",
        f"- Public brand rows with valuation data: {len(rows)}",
        f"- Unique public tickers with valuation data: {len(ticker_rows)}",
        "",
        "## Correlation Results",
        "",
        "Values are correlations between score and the log of the valuation multiple. The slope column approximates the percent change in the multiple associated with a 10-point higher score.",
        "",
        "### Brand Rows",
        "",
        "| Metric | N | Pearson | Spearman | Approx. p-value | R-squared | Slope per 10 score pts |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    lines.extend(summary_table_rows(row_level))
    lines.extend(
        [
            "",
            "### Unique Tickers",
            "",
            "| Metric | N | Pearson | Spearman | Approx. p-value | R-squared | Slope per 10 score pts |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    lines.extend(summary_table_rows(ticker_level))
    lines.extend(
        [
            "",
            "## Score Quartiles, Unique Ticker View",
            "",
            f"- Low-score group: score <= {first_quartile:.1f}, n = {len(low_score)}",
            f"- High-score group: score >= {third_quartile:.1f}, n = {len(high_score)}",
            "",
            "| Group | Median MCap / revenue | Median EV / revenue | Median EV / EBITDA |",
            "|---|---:|---:|---:|",
            quartile_row("Low score", low_score),
            quartile_row("High score", high_score),
            "",
            "## Regional Differences, Unique Ticker View",
            "",
            "Region is inferred from ticker suffix and currency, so this is listing geography rather than a definitive headquarters or sales-exposure geography.",
            "",
            "| Region | Tickers | Median Score | Median MCap / Revenue | Median EV / Revenue | Median EV / EBITDA | Score vs EV / Revenue Corr. |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in region_rows:
        lines.append(
            "| {region} | {unique_tickers} | {median_score} | {median_mcap_revenue} | {median_ev_revenue} | {median_ev_ebitda} | {corr_score_log_ev_revenue} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The full public-company sample shows only a weak positive relationship between transparency score and valuation multiples. In the cleaner unique-ticker view, the relationship becomes very small: score versus EV / revenue has a correlation around 0.12 and explains roughly 1.5% of variation in log EV / revenue.",
            "",
            "Geography matters more for score distribution than for a clear valuation effect. Europe ex-UK and the UK have higher median transparency scores than the US-listed group, but the UK has lower valuation multiples, suggesting sector mix, luxury exposure, growth expectations, margins, and parent-company business mix are likely stronger drivers.",
            "",
            "This is association, not causation. The next improvement would add explicit headquarters/listing country, industry category, growth, margin, and luxury-versus-retail controls.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def summary_table_rows(results: dict[str, dict[str, float | int | None]]) -> list[str]:
    rows = []
    for metric, result in results.items():
        slope = result["slope_per_10_score_pct"]
        rows.append(
            "| {metric} | {n} | {pearson} | {spearman} | {p_value} | {r2} | {slope} |".format(
                metric=metric,
                n=result["n"],
                pearson=format_number(result["pearson"]),
                spearman=format_number(result["spearman"]),
                p_value=format_number(result["p_approx"], digits=3),
                r2=format_number(result["r2"], digits=3),
                slope="" if slope is None else f"{slope:.1f}%",
            )
        )
    return rows


def quartile_row(label: str, rows: list[TickerRow]) -> str:
    return "| {label} | {mcap_rev} | {ev_rev} | {ev_ebitda} |".format(
        label=label,
        mcap_rev=format_number(median(row.mcap_revenue for row in rows)),
        ev_rev=format_number(median(row.ev_revenue for row in rows)),
        ev_ebitda=format_number(median(row.ev_ebitda for row in rows)),
    )


def main() -> None:
    rows = load_public_rows()
    ticker_rows = dedupe_by_ticker(rows)
    write_ticker_csv(ticker_rows)
    write_region_csv(summarize_by_region(ticker_rows))
    write_summary(rows, ticker_rows)
    print(f"Wrote {SUMMARY_MD}")
    print(f"Wrote {REGION_CSV}")
    print(f"Wrote {TICKER_CSV}")


if __name__ == "__main__":
    main()
