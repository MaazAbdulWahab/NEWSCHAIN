import joblib

loaded_model = joblib.load("model.pkl")
loaded_vectorizer = joblib.load("vectorizer.pkl")


def generate(text):
    new_data_vectorized = loaded_vectorizer.transform(text)

    predictions = loaded_model.predict(new_data_vectorized)

    return int(predictions)
