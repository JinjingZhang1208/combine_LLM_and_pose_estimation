import os
import math
import csv
import datetime
import numpy as np
import openai
from sentence_transformers import util
from collections import deque
from sklearn.preprocessing import MinMaxScaler
from openai.embeddings_utils import get_embeddings, get_embedding
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
openai.api_key = API_KEY


engine = "text-embedding-ada-002"
DECAY_FACTOR = 0.995
RECENCY_WEIGHT = 1.0
RELEVANCE_WEIGHT = 1.0

currStatement = ""
resultObservation = []


def retrievalFunction(
    currentConversation: str,
    memoryStream: list,
    retrievalCount: int,
    isBaseDescription=True,
):
    """
    For CSV only
    """
    global currStatement
    currStatement = currentConversation
    if memoryStream:
        memoryStream = calculateRecency(memoryStream, isBaseDescription)
        memoryData = prepareMemoryData(memoryStream)
        observationData = [memory[0] for memory in memoryData]
        recencyScores = [memory[1] for memory in memoryData]
        similarityScores = calculateRelevance(currentConversation, observationData)
        return calculateRetrievalScore(
            observationData, recencyScores, similarityScores, retrievalCount
        )
    return [""]


def calculateRecency(memoryStream, isBaseDescription):
    for memory in memoryStream:
        if isBaseDescription:
            memory["Recency"] = 0
        else:
            currTime = datetime.datetime.utcnow()
            diffInSeconds = (currTime - memory["Creation Time"]).total_seconds()
            minutesDiff = diffInSeconds / 3600
            memory["Recency"] = math.exp(-DECAY_FACTOR * minutesDiff)
    return memoryStream


def calculateRelevance(currentConversation: str, observationData: list):
    contentEmbedding = get_embedding(currentConversation, engine)
    dataEmbedding = get_embeddings(observationData, engine)
    similarityVector = util.pytorch_cos_sim(contentEmbedding, dataEmbedding).tolist()[0]
    return similarityVector


def scaleScores(relevantObservations: list) -> list:
    retrievalScores = np.array(
        [observation[0] for observation in relevantObservations]
    ).reshape(-1, 1)

    minMaxScaler = MinMaxScaler()
    retrievalScores = minMaxScaler.fit_transform(retrievalScores)

    relevantObservations = list(
        zip(
            retrievalScores.flatten(),
            [observation[1] for observation in relevantObservations],
        )
    )
    return relevantObservations


def calculateRetrievalScore(
    observationData: list,
    recencyScores: list,
    similarityVector: list,
    retrievalCount: int,
):
    global resultObservation
    relevantObservations = []
    for idx, simScore in enumerate(similarityVector):
        retrievalScore = (
            recencyScores[idx] * RECENCY_WEIGHT + simScore * RELEVANCE_WEIGHT
        )
        currObservation = (retrievalScore, observationData[idx])
        relevantObservations.append(currObservation)
    relevantObservations = scaleScores(relevantObservations)
    relevantObservations = sorted(
        relevantObservations, key=lambda x: x[0], reverse=True
    )[:retrievalCount]
    resultObservation = relevantObservations
    updateCSV()
    return relevantObservations


def prepareMemoryData(memoryStream):
    memoryData = []
    for memory in memoryStream:
        recency = memory["Recency"]
        for observation in memory["Observations"]:
            memoryData.append((observation, recency))
    return memoryData


testQueue = deque(
    [
        {
            "Username": "John Lin",
            "Conversation with User": "Katie",
            "Creation Time": datetime.datetime(2023, 9, 30, 17, 58, 0, 928673),
            "Observations": [
                "Katie and John are discussing their living situations.",
                "John values family and views them as important.",
                "John shows interest in Katie's living situation.",
            ],
        },
        {
            "Username": "John Lin",
            "Conversation with User": "Katie",
            "Creation Time": datetime.datetime(2023, 9, 30, 17, 57, 43, 829009),
            "Observations": [
                "John Lin has a son named Eddy who is studying music theory.",
                "John Lin loves his family very much.",
                "John Lin asks Katie if she has any kids.",
            ],
        },
        {
            "Username": "John Lin",
            "Conversation with User": "Katie",
            "Creation Time": datetime.datetime(2023, 9, 30, 17, 57, 32, 155953),
            "Observations": [
                "John Lin values his family a lot.",
                "John Lin has a wife named Mei Lin.",
            ],
        },
    ]
)


def updateCSV():
    csvData = []
    global resultObservation
    global currStatement
    headers = ["Current Statement", "Relevant observation", "Score"]
    for observation in resultObservation:
        currData = {
            "Current Statement": currStatement,
            "Relevant observation": observation[1],
            "Score": observation[0],
        }
        csvData.append(currData)
    currFile = (
        f"DF_{DECAY_FACTOR}_RECW_{RECENCY_WEIGHT}_RELW_{RELEVANCE_WEIGHT}_retCount5.csv"
    )
    with open(
        currFile,
        "a+",
        newline="",
        encoding="utf-8",
    ) as csvFile:
        csvWriter = csv.DictWriter(csvFile, fieldnames=headers)
        if not os.path.exists(currFile):
            csvWriter.writeheader()
        csvWriter.writerows(csvData)


# print(retrievalFunction("Hi John! tell me about your familly", testQueue, 5, True))
