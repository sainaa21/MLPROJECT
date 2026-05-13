import pandas as pd

from app.preprocessing.clean_text import clean_comment

df = pd.read_csv("data/raw/comments.csv")

print(df.columns)

df = df[['comment']]

df.dropna(inplace=True)

df = df[df['comment'].str.strip() != ""]

df['cleaned_comment'] = df['comment'].apply(clean_comment)

df.drop_duplicates(subset=['cleaned_comment'], inplace=True)

df = df[df['cleaned_comment'].str.strip() != ""]

df.to_csv(
    "data/processed/cleaned_comments.csv",
    index=False
)

print("✅ Preprocessing Complete!")
print(df.head())