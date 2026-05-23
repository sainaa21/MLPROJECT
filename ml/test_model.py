import joblib

from app.preprocessing.preprocess import clean_comment

model = joblib.load(
    "models/spam_model.pkl"
)

vectorizer = joblib.load(
    "models/tfidf_vectorizer.pkl"
)

while True:

    text = input("\nEnter Comment: ")

    cleaned = clean_comment(text)

    vector = vectorizer.transform([cleaned])

    prediction = model.predict(vector)[0]

    probability = model.predict_proba(vector)[0]

    spam_confidence = probability[1]

    if prediction == 1:
        result = "SPAM"
    else:
        result = "NOT SPAM"

    print("\nPrediction:", result)

    print("Spam Confidence:", round(spam_confidence * 100, 2), "%")