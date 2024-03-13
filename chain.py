import multichain
import json
import pandas as pd
import random

from generatePrediction import generate
from utils import generate_random_string
import hashlib
import datetime
import time

### Create Connection
rpcuser = "multichainrpc"
rpcpassword = "D2UbRkoaprz1ex7wXqgUA2YC3GYN9Xq4diKwpHTJzvvG"
rpchost = "127.0.0.1"
rpcport = "6828"
chainname = "NEWSCHAIN"
mc = multichain.MultiChainClient(rpchost, rpcport, rpcuser, rpcpassword)

### We created some addresses using UI and designate some as publishers and some as validators

publisherAddresses = [
    "15dK5rLNS7a269GBXJ6W4Z86AYCVH4JvnVPq53",
    "1TYgj2L84cr92o6Hih2CCpAUjw3N3r2GaeJyoK",
]
validatorAddresses = [
    "1J19jG3euXPbmtcrzvH8kfc2NMcqJsPo2NuQHb",
    "12xVC1u4oo8CD4PY1WqZP1aCXAZvFhVF4zeJ5W",
    "12xVC1u4oo8CD4PY1WqZP1aCXAZvFhVF4zeJ5W",
]

### We require 4 distinct streams
# 1. For publishing news
# 2. For publishin validations
# 3. For publishing final article in case it passes all validations
# 4. For putting unique identifier for news

streamPublishing = "PUBLISHED"
streamValidations = "VALIDATIONS"
streamFinalPublication = "PUBLISHED_FINAL"
streamUniqueIdentifiersNews = "NEWSIDS"


### Create streams and subscribe to it.

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

### Picking up 10 random news from files.

data = pd.read_csv("WELFake_Dataset.csv")


data = data.dropna()

toPick = [random.randint(0, 50000) for i in range(10)]
sample = data.iloc[toPick]


### For each of the random picking, we push it to publishing stream,
### with the address of publisher and its signature.
### Its unique identifer is also being pushed to unique identifier stream

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


### We mimic the picking up of last few news items (last 2 minutes)

recents = mc.liststreamkeyitems(
    streamUniqueIdentifiersNews, "IDENTIFIERS", False, 100, -100
)
now = datetime.datetime.now().timestamp()
time.sleep(2)
recents = list(
    filter(
        lambda x: dict(x).get("blocktime") and dict(x)["blocktime"] > now - 60, recents
    )
)
print("Picked Recents are")
for r in recents:
    print(dict(r)["data"].get("text"))

### For all those recent news pickups , we let validators score them for fakeness
### and push their verdict to validation stream.

for r in recents:
    identifier = dict(r)["data"].get("text")
    if identifier:
        findNews = mc.liststreamkeyitems(streamPublishing, identifier)

        news = dict(findNews[0])["data"].get("json")
        if not news:
            continue
        ## We have the news here and after that , we let all the
        ## validators score them

        news = news.get("news")
        for vals in validatorAddresses:
            ## Currently all validators use the same scoring function
            ## Verdicts are pushed on the validation stream.
            print("Validator Address")
            print(vals)
            print("News Identifier")
            print(identifier)
            print("Prediction")
            prediction = generate([news])
            print(prediction)
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

### Now again for all those recents

print("Final System Phase")
for r in recents:
    identifier = dict(r)["data"].get("text")
    ### get recent identifiers
    if identifier:
        ### pull out all validator verdicts
        ### in our system , trust is an asset , which is used for taking
        ### weighting average of verdict score
        ### trust can be increased or decreased
        print("Identifier")
        print(identifier)
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
            print("score Overall")
            print(scoreOverall)
            ### overall positive verdict will be pushed in the final publication
            ### stream.
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
