import multichain
import json
import pandas as pd
import random

from generatePrediction import generate
from utils import generate_random_string
import hashlib
import datetime


rpcuser = "multichainrpc"
rpcpassword = "D2UbRkoaprz1ex7wXqgUA2YC3GYN9Xq4diKwpHTJzvvG"
rpchost = "127.0.0.1"
rpcport = "6828"
chainname = "NEWSCHAIN"
mc = multichain.MultiChainClient(rpchost, rpcport, rpcuser, rpcpassword)

publisherAddresses = [
    "15dK5rLNS7a269GBXJ6W4Z86AYCVH4JvnVPq53",
    "1TYgj2L84cr92o6Hih2CCpAUjw3N3r2GaeJyoK",
]
validatorAddresses = [
    "1J19jG3euXPbmtcrzvH8kfc2NMcqJsPo2NuQHb",
    "12xVC1u4oo8CD4PY1WqZP1aCXAZvFhVF4zeJ5W",
    "12xVC1u4oo8CD4PY1WqZP1aCXAZvFhVF4zeJ5W",
]

streamPublishing = "PUBLISHED"
streamValidations = "VALIDATIONS"
streamFinalPublication = "PUBLISHED_FINAL"
streamUniqueIdentifiersNews = "NEWSIDS"


if not mc.liststreams(streamPublishing):
    mc.create("stream", streamPublishing, True)

if not mc.liststreams(streamValidations):
    mc.create("stream", streamValidations, True)

if not mc.liststreams(streamFinalPublication):
    mc.create("stream", streamFinalPublication, True)

if not mc.liststreams(streamUniqueIdentifiersNews):
    mc.create("stream", streamUniqueIdentifiersNews, True)

mc.subscribe(
    [
        streamFinalPublication,
        streamPublishing,
        streamValidations,
        streamUniqueIdentifiersNews,
    ]
)
"""
data = pd.read_csv("WELFake_Dataset.csv")


data = data.dropna()

toPick = [random.randint(0, 50000) for i in range(10)]
sample = data.iloc[toPick]

for index, row in sample.iterrows():
    identifer = generate_random_string(10)
    addressPublishing = random.choice(publisherAddresses)
    mc.publish(
        streamPublishing,
        identifer,
        {
            "json": {
                "news": row["text"],
                "address": addressPublishing,
                "signature": hashlib.md5(addressPublishing.encode()).hexdigest(),
            }
        },
    )
    mc.publish(streamUniqueIdentifiersNews, "IDENTIFIERS", {"text": identifer})

"""
recents = mc.liststreamkeyitems(
    streamUniqueIdentifiersNews, "IDENTIFIERS", False, 100, -100
)
now = datetime.datetime.now().timestamp()
recents = list(filter(lambda x: dict(x)["blocktime"] > now - 3600, recents))

for r in recents:
    identifier = dict(r)["data"].get("text")
    if identifier:
        findNews = mc.liststreamkeyitems(streamPublishing, identifier)

        news = dict(findNews[0])["data"].get("json")
        if not news:
            continue
        news = news.get("news")
        for vals in validatorAddresses:
            prediction = generate([news])
            mc.publish(
                streamValidations,
                identifier,
                {
                    "json": {
                        "address": vals,
                        "signature": hashlib.md5(vals.encode()).hexdigest(),
                        "verdict": prediction,
                    }
                },
            )


for r in recents:
    identifier = dict(r)["data"].get("text")
    if identifier:
        findVerdicts = mc.liststreamkeyitems(streamValidations, identifier)
        numerator = 0
        denominator = 0
        for ver in findVerdicts:

            validatorAddress = dict(ver)["data"]["json"]["address"]
            trust = dict(mc.getaddressbalances(validatorAddress, 0)[0])["qty"]
            verdict = dict(ver)["data"]["json"]["verdict"]
            numerator += trust * verdict
            denominator += trust
        try:
            scoreOverall = float(numerator) / float(denominator)

            if scoreOverall >= 0.5:
                mc.publish(
                    streamFinalPublication,
                    identifier,
                    {
                        "json": {
                            "verdict": scoreOverall,
                        }
                    },
                )
        except:
            pass
