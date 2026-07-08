"""
Manual brand-tier classification used by stock_return_analysis.py.

The source dataset has no price-tier or category field, so brands are
assigned by hand to one of four tiers based on market positioning:
luxury, designer, mid-level, or fast fashion. General retailers, grocery
chains, department stores, and marketplaces are left unclassified (None)
since they are not fashion brands in a single price tier.

This is a judgment call, not a published taxonomy. Boundaries between
"luxury" and "designer", or "mid-level" and "fast fashion", are fuzzy in
places (e.g. Massimo Dutti, Canada Goose, UGG). Treat tier assignment as
approximate.
"""

from __future__ import annotations

LUXURY = {
    "Hermes", "Chanel", "Louis Vuitton", "Dior", "CELINE", "Gucci", "Prada",
    "Miu Miu", "Balenciaga", "Bottega Veneta", "SAINT LAURENT", "Fendi",
    "Valentino", "Marni", "Jil Sander", "Tod's", "Furla", "Longchamp",
    "Max Mara", "Tom Ford", "Dolce & Gabbana", "Versace", "Armani",
    "Burberry", "Moncler", "Brunello Cucinelli", "Ermenegildo Zegna",
    "Salvatore Ferragamo", "Bally",
}

DESIGNER = {
    "Marc Jacobs", "Carolina Herrera", "Chloe", "COACH", "Kate Spade",
    "Michael Kors", "Tory Burch", "DKNY", "BCBGMAXAZRIA", "Diesel", "GUESS",
    "Ted Baker", "Canada Goose", "G-Star RAW", "Nine West",
}

MID_LEVEL = {
    "Nike", "Adidas", "Puma", "Under Armour", "Lululemon", "New Balance",
    "ASICS", "Skechers", "Columbia Sportswear", "The North Face",
    "Timberland", "Vans", "Converse", "Jordan", "Champion", "Hanes",
    "Carhartt", "Wrangler", "Levi Strauss & Co", "Calvin Klein",
    "Tommy Hilfiger", "Ralph Lauren", "Gap", "Banana Republic", "Old Navy",
    "Abercrombie & Fitch", "Hollister Co.", "American Eagle", "Aeropostale",
    "Express", "Chico's", "Anthropologie", "Free People", "Urban Outfitters",
    "Steve Madden", "Aritzia", "Sandro", "Esprit", "s.Oliver", "Lacoste",
    "UGG", "Speedo", "Fossil", "Clarks", "Dr. Martens", "Fila", "ALDO",
    "Foot Locker", "DSW", "Famous Footwear", "Buckle", "Nordstrom",
    "Macy's", "Bloomingdale's", "Dillard's", "Kohl's", "TJ Maxx",
    "Burlington", "Ross Dress for Less", "Marks & Spencer", "Next",
    "John Lewis", "River Island", "Sports Direct", "JD Sports", "Gymshark",
    "Fanatics", "Mizuno", "Brooks Sport", "Helly Hansen", "Jack Wolfskin",
    "Fjallraven", "Mammut", "Patagonia", "Kathmandu", "Merrell",
    "Eddie Bauer", "LL Bean", "REI", "Tommy Bahama", "Billabong",
    "Quiksilver", "Roxy", "Jockey", "Gildan", "Fruit of the Loom",
    "Russell Athletic", "Reebok", "Lands' End", "Massimo Dutti",
    "United Arrows", "Superdry",
}

FAST_FASHION = {
    "Zara", "Bershka", "Pull&Bear", "Stradivarius", "H&M", "Uniqlo", "GU",
    "Primark", "ASOS", "boohoo", "PrettyLittleThing", "SHEIN",
    "Fashion Nova", "Romwe", "New Yorker", "Tom Tailor", "Reserved", "C&A",
    "OVS", "Cotton On", "Mango", "Vero Moda", "Jack & Jones", "New Look",
    "Kiabi", "Pimkie", "Monoprix", "Takko", "LC Waikiki", "Shimammura",
    "Matalan", "TOPVALU COLLECTION", "Joe Fresh", "The Children's Place",
    "The Warehouse", "Foschini", "KIK", "REVOLVE", "Fabletics", "Zalando",
}

TIER_ORDER = ["Luxury", "Designer", "Mid-Level", "Fast Fashion"]


def classify(company: str) -> str | None:
    if company in LUXURY:
        return "Luxury"
    if company in DESIGNER:
        return "Designer"
    if company in MID_LEVEL:
        return "Mid-Level"
    if company in FAST_FASHION:
        return "Fast Fashion"
    return None
