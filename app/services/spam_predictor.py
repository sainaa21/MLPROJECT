import joblib

from app.preprocessing.preprocess import clean_text

model = joblib.load(
    "models/spam_model.pkl"
)

vectorizer = joblib.load(
    "models/tfidf_vectorizer.pkl"
)


def predict_spam(text):

    cleaned = clean_text(text)

    vector = vectorizer.transform([cleaned])

    prediction = model.predict(vector)[0]

    probability = model.predict_proba(vector)[0]

    spam_confidence = probability[1]

    result = (
        "spam"
        if prediction == 1
        else "not spam"
    )

    return {
        "prediction": result,
        "spam_confidence": round(
            spam_confidence * 100,
            2
        )
    }