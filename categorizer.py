import pandas as pd

CATEGORY_RULES = {
    "food": ["swiggy", "zomato", "restaurant", "cafe", "pizza", "burger", "diner", "grocery", "supermarket", "bigbasket"],
    "transport": ["uber", "ola", "rapido", "metro", "petrol", "fuel", "parking", "irctc", "makemytrip"],
    "rent": ["rent", "pg", "hostel", "landlord", "house"],
    "entertainment": ["netflix", "spotify", "prime", "hotstar", "youtube", "cinema", "pvr", "inox", "game"],
    "utilities": ["electricity", "water", "internet", "jio", "airtel", "bsnl", "vi", "broadband"],
    "shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa", "mall"],
    "health": ["pharmacy", "hospital", "clinic", "doctor", "medplus", "apollo", "1mg", "netmeds"],
}

def categorizer(description: str) -> str:
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in desc for kw in keywords):
            return category
    return "other"


def categorizer_df(df):
    df = df.copy()
    df["category"] = df["description"].apply(categorizer)
    return df


def spending_by_category(df):
    summary = (
        df.groupby("category")["amount"]
        .agg(total="sum", count="count")
        .reset_index()
        .sort_values("total", ascending=False)
        .round(2)
    )
    return summary