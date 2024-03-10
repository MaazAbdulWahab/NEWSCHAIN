import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib


df = pd.read_csv("WELFake_Dataset.csv")
df = df.dropna()
print(df.info())
print("Split data into train and test sets")
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42
)


print("Initializing Vectorizer")
vectorizer = TfidfVectorizer()
print("Vectorizing")
X_train_vectorized = vectorizer.fit_transform(X_train)
X_test_vectorized = vectorizer.transform(X_test)

print("Model Initialization and fitting")
clf = LogisticRegression()
clf.fit(X_train_vectorized, y_train)

print("Testing on test set")
y_pred = clf.predict(X_test_vectorized)

print("Accuracy on test set")
accuracy = accuracy_score(y_test, y_pred)
print("Accuracy:", accuracy)


print("Testing on train set")
y_pred_train = clf.predict(X_train_vectorized)

print("Accuracy on train set")
accuracy = accuracy_score(y_train, y_pred_train)
print("Accuracy:", accuracy)
joblib.dump(clf, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
