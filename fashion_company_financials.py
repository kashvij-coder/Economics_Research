"""
Fashion Transparency Index scores plus Yahoo Finance enrichment.

The scores below were transcribed from the two screenshots supplied on
2026-05-03. Yahoo Finance data is fetched where a public ticker is available or
where Yahoo's search endpoint can resolve a brand/company to an equity quote.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


YAHOO_TIMESERIES_TYPES = ",".join(
    [
        "trailingMarketCap",
        "trailingTotalRevenue",
        "trailingEBITDA",
        "quarterlyTotalDebt",
    ]
)
OUT_JSON = Path("fashion_company_financials_output.json")
OUT_CSV = Path("fashion_company_financials_output.csv")


@dataclass
class FashionCompany:
    company: str
    fashion_index_score: int
    ticker: str | None = None
    yahoo_name: str | None = None
    market_cap: int | None = None
    revenue: int | None = None
    ebitda: int | None = None
    debt: int | None = None
    currency: str | None = None
    yahoo_resolution_note: str | None = None


SCORES: list[tuple[str, int]] = [
    ("Reliance Trends", 10), ("Costco", 10), ("Tommy Bahama", 10),
    ("Saks Fifth Avenue", 9), ("Foot Locker", 9), ("Famous Footwear", 9),
    ("Tod's", 9), ("Li-Ning", 9), ("Hudson's Bay", 9), ("LL Bean", 8),
    ("Gerry Weber", 8), ("Merrell", 8), ("ALDI", 8), ("Carhartt", 7),
    ("Truworths", 7), ("Triumph", 7), ("Takko", 7), ("Sports Direct", 7),
    ("DSW", 7), ("Beanpole", 7), ("Bloomingdale's", 7), ("Macy's", 7),
    ("SHEIN", 7), ("Skechers", 7), ("Kmart", 6), ("Billabong", 6),
    ("Quiksilver", 6), ("Roxy", 6), ("Ross Dress for Less", 6),
    ("Express", 6), ("Furla", 5), ("Eddie Bauer", 5), ("CAROLL", 5),
    ("Buckle", 4), ("Shimammura", 4), ("LC Waikiki", 4), ("Dillard's", 3),
    ("Aeropostale", 3), ("Romwe", 3), ("Longchamp", 2), ("Pepe Jeans", 2),
    ("Deichmann", 2), ("Jockey", 2), ("Dolce & Gabbana", 2),
    ("REVOLVE", 2), ("Fabletics", 2), ("BCBGMAXAZRIA", 1), ("Reebok", 1),
    ("Max", 1), ("celio", 1), ("DKNY", 1), ("Nine West", 1),
    ("Tory Burch", 1), ("Splash", 0), ("Fashion Nova", 0),
    ("Max Mara", 0), ("New Yorker", 0), ("Tom Ford", 0), ("ANTA", 0),
    ("Bosideng", 0), ("Helian Home", 0), ("Belle", 0),
    ("Big Bazaar - ffb", 0), ("Semir", 0), ("Van Heusen", 0),
    ("K-Way", 0), ("KOOVS", 0), ("Metersbonwe", 0), ("Mexx", 0),
    ("Savage X Fenty", 0), ("Youngor", 0),
    ("Reserved", 20), ("Otto", 20), ("Diesel", 19),
    ("Victoria's Secret", 19), ("Pimkie", 18), ("Foschini", 18),
    ("Mizuno", 18), ("Joe Fresh", 18), ("Fanatics", 18),
    ("Jil Sander", 18), ("Monoprix", 18), ("Valentino", 18),
    ("The Warehouse", 17), ("Clarks", 17), ("Marni", 17),
    ("The Children's Place", 17), ("Kohl's", 17), ("KIK", 17),
    ("United Arrows", 17), ("Kiabi", 16), ("Fossil", 16),
    ("Carolina Herrera", 16), ("Canada Goose", 16), ("Fila", 15),
    ("Burlington", 14), ("ALDO", 14), ("Brunello Cucinelli", 14),
    ("Chico's", 14), ("TOPVALU COLLECTION", 13), ("TJ Maxx", 13),
    ("Anthropologie", 13), ("Free People", 13), ("Urban Outfitters", 13),
    ("Steve Madden", 13), ("La Redoute", 13), ("Lands' End", 12),
    ("Kaufland", 12), ("Ito-Yokado", 11), ("MFB", 11),
    ("Falabella", 11), ("Chanel", 11),
    ("Helly Hansen", 30), ("CELINE", 30), ("JD Sports", 29),
    ("Matalan", 29), ("Woolworths South Africa", 29), ("Dior", 29),
    ("Kathmandu", 29), ("Louis Vuitton", 29), ("Morrisons", 29),
    ("Marc Jacobs", 28), ("Muji", 28), ("Asda", 28), ("Hermes", 28),
    ("Under Armour", 28), ("Dick's Sporting Goods", 27), ("Very", 27),
    ("Gymshark", 27), ("Moncler", 27), ("Nordstrom", 26),
    ("Decathlon", 26), ("Ted Baker", 26), ("Amazon", 26), ("Lidl", 25),
    ("Paris", 25), ("Desigual", 25), ("Jack Wolfskin", 25),
    ("Carter's", 25), ("boohoo", 24), ("PrettyLittleThing", 24),
    ("Salvatore Ferragamo", 24), ("El Corte Ingles", 24), ("HEMA", 24),
    ("Carrefour", 24), ("Versace", 24), ("Michael Kors", 23),
    ("Walmart", 23), ("Prisma", 22), ("Disney", 22), ("Cotton On", 22),
    ("Aritzia", 22), ("Sandro", 22), ("REI", 22), ("American Eagle", 21),
    ("Cortefiel", 21),
    ("Fjallraven", 40), ("Zalando", 40), ("Patagonia", 40),
    ("Primark", 40), ("Big W", 39), ("Armani", 38), ("Burberry", 38),
    ("Marks & Spencer", 38), ("Champion", 38), ("Lacoste", 38),
    ("Hanes", 38), ("Bonprix", 37), ("Target", 37),
    ("Columbia Sportswear", 37), ("Next", 36), ("Brooks Sport", 36),
    ("Dr. Martens", 35), ("Mammut", 35), ("ALDI SOUTH", 34),
    ("Miu Miu", 34), ("Prada", 34), ("Fruit of the Loom", 34),
    ("Russell Athletic", 34), ("Abercrombie & Fitch", 33),
    ("Hollister Co.", 33), ("Bally", 33), ("Wrangler", 33),
    ("Ermenegildo Zegna", 33), ("John Lewis", 32), ("River Island", 32),
    ("ALDI Nord", 31), ("GUESS", 31),
    ("Tom Tailor", 50), ("ASOS", 50), ("Converse", 50), ("Jordan", 50),
    ("Nike", 50), ("Bershka", 50), ("Massimo Dutti", 50),
    ("Pull&Bear", 50), ("Stradivarius", 50), ("Zara", 50),
    ("Tommy Hilfiger", 50), ("G-Star RAW", 49), ("Mango", 49),
    ("Superdry", 49), ("Banana Republic", 48), ("Gap", 48),
    ("Old Navy", 48), ("Calvin Klein", 48), ("Tesco", 48),
    ("Speedo", 47), ("New Balance", 46), ("ASICS", 45), ("Esprit", 45),
    ("Lindex", 44), ("Chloe", 43), ("Tchibo", 43), ("s.Oliver", 43),
    ("New Look", 42), ("COACH", 42), ("Jack & Jones", 41),
    ("Vero Moda", 41), ("Kate Spade", 41),
    ("Levi Strauss & Co", 60), ("Fendi", 58), ("UGG", 57), ("Adidas", 56),
    ("Hugo Boss", 55), ("Ralph Lauren", 54), ("Zeeman", 54),
    ("Gildan", 54), ("Lululemon", 52), ("Sainsbury's", 51),
    ("Balenciaga", 51), ("Bottega Veneta", 51), ("SAINT LAURENT", 51),
    ("GU", 51), ("Uniqlo", 51),
    ("C&A", 68), ("Puma", 66), ("The North Face", 66),
    ("Timberland", 66), ("Vans", 65), ("Dressmann", 65),
    ("Calzedonia", 63), ("Intimissimi", 63), ("Tezenis", 63),
    ("Gucci", 80), ("Kmart Australia", 76), ("Target Australia", 76),
    ("United Colors of Benetton", 73), ("H&M", 71), ("OVS", 83),
]


# Explicit mappings are safer than blind search, especially for brands owned by
# larger public groups. Subsidiary brands use the parent's Yahoo ticker.
KNOWN_TICKERS: dict[str, str] = {
    "Costco": "COST", "Li-Ning": "2331.HK",
    "Macy's": "M", "Kmart": "WES.AX",
    "Ross Dress for Less": "ROST", "Dillard's": "DDS",
    "REVOLVE": "RVLV", "DKNY": "GIII", "Tory Burch": "TPR",
    "ANTA": "2020.HK", "Bosideng": "3998.HK", "Semir": "002563.SZ",
    "Victoria's Secret": "VSCO", "Mizuno": "8022.T",
    "The Warehouse": "WHS.NZ", "Kohl's": "KSS", "United Arrows": "7606.T",
    "Fossil": "FOSL", "Canada Goose": "GOOS", "Burlington": "BURL",
    "Brunello Cucinelli": "BC.MI",
    "TJ Maxx": "TJX", "Anthropologie": "URBN", "Free People": "URBN",
    "Urban Outfitters": "URBN", "Steve Madden": "SHOO", "Lands' End": "LE",
    "Ito-Yokado": "3382.T", "Falabella": "FALABELLA.SN",
    "CELINE": "MC.PA", "JD Sports": "JD.L", "Dior": "CDI.PA",
    "Kathmandu": "KMD.NZ", "Louis Vuitton": "MC.PA",
    "Marc Jacobs": "MC.PA", "Hermes": "RMS.PA", "Under Armour": "UAA",
    "Dick's Sporting Goods": "DKS", "Moncler": "MONC.MI",
    "Amazon": "AMZN", "Carter's": "CRI",
    "boohoo": "DEBS.L", "PrettyLittleThing": "DEBS.L",
    "Salvatore Ferragamo": "SFER.MI", "Carrefour": "CA.PA",
    "Versace": "CPRI", "Michael Kors": "CPRI", "Walmart": "WMT",
    "Disney": "DIS", "Aritzia": "ATZ.TO", "American Eagle": "AEO",
    "Zalando": "ZAL.DE", "Big W": "WOW.AX", "Burberry": "BRBY.L",
    "Marks & Spencer": "MKS.L", "Target": "TGT",
    "Columbia Sportswear": "COLM", "Next": "NXT.L",
    "Dr. Martens": "DOCS.L", "Prada": "1913.HK",
    "Abercrombie & Fitch": "ANF", "Hollister Co.": "ANF",
    "Ermenegildo Zegna": "ZGN", "ASOS": "ASC.L",
    "Converse": "NKE", "Jordan": "NKE", "Nike": "NKE",
    "Bershka": "ITX.MC", "Massimo Dutti": "ITX.MC", "Pull&Bear": "ITX.MC",
    "Stradivarius": "ITX.MC", "Zara": "ITX.MC",
    "Tommy Hilfiger": "PVH",
    "Banana Republic": "GAP", "Gap": "GAP", "Old Navy": "GAP",
    "Calvin Klein": "PVH", "Tesco": "TSCO.L", "ASICS": "7936.T",
    "Chloe": "CFR.SW", "COACH": "TPR", "Kate Spade": "TPR",
    "Levi Strauss & Co": "LEVI", "Fendi": "MC.PA", "UGG": "DECK",
    "Adidas": "ADS.DE", "Hugo Boss": "BOSS.DE", "Ralph Lauren": "RL",
    "Gildan": "GIL", "Lululemon": "LULU", "Sainsbury's": "SBRY.L",
    "Balenciaga": "KER.PA", "Bottega Veneta": "KER.PA",
    "SAINT LAURENT": "KER.PA", "GU": "9983.T", "Uniqlo": "9983.T",
    "Puma": "PUM.DE", "The North Face": "VFC", "Timberland": "VFC",
    "Vans": "VFC", "Gucci": "KER.PA", "Kmart Australia": "WES.AX",
    "Target Australia": "WES.AX",
    "H&M": "HM-B.ST", "OVS": "OVS.MI",
}


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _reported_value(entry: dict[str, Any] | None) -> int | None:
    if not isinstance(entry, dict):
        return None
    raw = entry.get("reportedValue", {}).get("raw")
    if isinstance(raw, (int, float)):
        return int(raw)
    return None


def search_yahoo_ticker(company: str) -> tuple[str | None, str | None]:
    encoded = urllib.parse.quote(company)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={encoded}&quotesCount=6&newsCount=0"
    payload = _get_json(url)
    for quote in payload.get("quotes", []):
        if quote.get("quoteType") == "EQUITY" and quote.get("symbol"):
            return quote["symbol"], quote.get("shortname") or quote.get("longname")
    return None, None


def fetch_yahoo_financials(ticker: str) -> dict[str, Any]:
    encoded_ticker = urllib.parse.quote(ticker)
    url = (
        "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/"
        f"timeseries/{encoded_ticker}?type={YAHOO_TIMESERIES_TYPES}"
        "&merge=false&period1=1600000000&period2=1893456000"
    )
    result = _get_json(url)["timeseries"]["result"]
    values: dict[str, int | None] = {
        "market_cap": None,
        "revenue": None,
        "ebitda": None,
        "debt": None,
    }
    currency: str | None = None

    type_to_field = {
        "trailingMarketCap": "market_cap",
        "trailingTotalRevenue": "revenue",
        "trailingEBITDA": "ebitda",
        "quarterlyTotalDebt": "debt",
    }
    for item in result:
        data_type = item.get("meta", {}).get("type", [None])[0]
        field = type_to_field.get(data_type)
        if not field:
            continue
        entries = item.get(data_type, [])
        latest = entries[-1] if entries else None
        values[field] = _reported_value(latest)
        currency = currency or (latest or {}).get("currencyCode")

    chart_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_ticker}?range=1d&interval=1d"
    chart_meta = _get_json(chart_url)["chart"]["result"][0]["meta"]
    currency = currency or chart_meta.get("currency")

    return {
        "market_cap": values["market_cap"],
        "revenue": values["revenue"],
        "ebitda": values["ebitda"],
        "debt": values["debt"],
        "currency": currency,
        "yahoo_name": chart_meta.get("longName") or chart_meta.get("shortName"),
    }


def build_companies() -> list[FashionCompany]:
    return [
        FashionCompany(company=name, fashion_index_score=score, ticker=KNOWN_TICKERS.get(name))
        for name, score in SCORES
    ]


def enrich_companies(delay_seconds: float = 0.25, use_search: bool = False) -> list[FashionCompany]:
    companies = build_companies()
    for company in companies:
        if not company.ticker and use_search:
            try:
                company.ticker, company.yahoo_name = search_yahoo_ticker(company.company)
                company.yahoo_resolution_note = "auto-resolved by Yahoo search" if company.ticker else None
                time.sleep(delay_seconds)
            except (urllib.error.URLError, KeyError, TimeoutError, json.JSONDecodeError) as error:
                company.yahoo_resolution_note = f"ticker search failed: {error}"

        if not company.ticker:
            company.yahoo_resolution_note = company.yahoo_resolution_note or "no public Yahoo ticker found"
            continue

        try:
            yahoo_data = fetch_yahoo_financials(company.ticker)
            company.market_cap = yahoo_data["market_cap"]
            company.revenue = yahoo_data["revenue"]
            company.ebitda = yahoo_data["ebitda"]
            company.debt = yahoo_data["debt"]
            company.currency = yahoo_data["currency"]
            company.yahoo_name = company.yahoo_name or yahoo_data["yahoo_name"]
            company.yahoo_resolution_note = company.yahoo_resolution_note or "mapped ticker"
            time.sleep(delay_seconds)
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError, json.JSONDecodeError) as error:
            company.yahoo_resolution_note = f"financial fetch failed: {error}"

    return companies


def write_outputs(companies: list[FashionCompany]) -> None:
    rows = [asdict(company) for company in companies]
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    enriched_companies = enrich_companies()
    write_outputs(enriched_companies)
    print(json.dumps([asdict(company) for company in enriched_companies], indent=2))
