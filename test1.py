import sys
sys.path.append('.')

from src.parser import parse_statement, summary
from src.categorizer import categorizer_df, spending_by_category

df = parse_statement("data/sample_statement.csv")
df = categorizer_df(df)
print(df)
print(spending_by_category(df))