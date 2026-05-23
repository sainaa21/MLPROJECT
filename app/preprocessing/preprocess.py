import pandas as pd
import re
import string

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

stop_words = set(ENGLISH_STOP_WORDS)


def clean_comment(text):

    text = str(text)

    text = text.lower()

    text = re.sub(r"http\S+", "", text)

    text = re.sub(r"[@#]\w+", "", text)

    text = text.translate(
        str.maketrans('', '', string.punctuation)
    )

    text = re.sub(r"\d+", "", text)

    words = text.split()

    words = [
        word for word in words
        if word not in stop_words
    ]

    cleaned_text = " ".join(words)

    return cleaned_text


df = pd.read_csv("data/raw/comments.csv")

print(df.columns)

df = df[['comment']]

df.dropna(inplace=True)

df = df[
    df['comment'].str.strip() != ""
]

df['cleaned_comment'] = df[
    'comment'
].apply(clean_comment)

df.drop_duplicates(
    subset=['cleaned_comment'],
    inplace=True
)

df = df[
    df['cleaned_comment'].str.strip() != ""
]

df.to_csv(
    "data/processed/cleaned_comments.csv",
    index=False
)

print("✅ Preprocessing Complete!")

print(df.head())