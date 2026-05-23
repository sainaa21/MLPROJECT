import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.linear_model import LogisticRegression

from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report

from app.preprocessing.preprocess import clean_comment

df = pd.read_csv("data/raw/spam.csv")

print("\nDataset Loaded Successfully\n")

print(df.head())

print("\nColumns:\n")

print(df.columns)

df["cleaned"] = df["CONTENT"].apply(clean_comment)

print("\nText Cleaning Done\n")

X = df["cleaned"]

y = df["CLASS"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("\nTrain Test Split Done\n")

vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2)
)

X_train_tfidf = vectorizer.fit_transform(X_train)

X_test_tfidf = vectorizer.transform(X_test)

print("\nTF-IDF Vectorization Done\n")

model = LogisticRegression(
    class_weight="balanced",
    max_iter=1000
)

model.fit(
    X_train_tfidf,
    y_train
)

print("\nModel Training Complete\n")

predictions = model.predict(X_test_tfidf)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nAccuracy:\n")

print(accuracy)

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        predictions
    )
)

os.makedirs("models", exist_ok=True)

joblib.dump(
    model,
    "models/spam_model.pkl"
)

joblib.dump(
    vectorizer,
    "models/tfidf_vectorizer.pkl"
)

print("\nModel Saved Successfully\n")