import pandas as pd


data = pd.read_csv("WELFake_Dataset.csv")

data = data.dropna()
data = data.head(1000)

data.to_csv("SAMPLE_Dataset.csv")
