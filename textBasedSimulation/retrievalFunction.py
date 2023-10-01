from glob import glob
import math
import csv
import datetime
from collections import deque
from heapq import heapify, heappushpop
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
DECAY_FACTOR = 0.05
RECENCY_WEIGHT = 0.3
RELEVANCE_WEIGHT = 0.7

csvData = []
currStatement = ""


def retrievalFunction(
    currentConversation: str,
    memoryStream: list,
    retrievalCount: int,
    isBaseDescription=True,
):
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
    return []


def calculateRecency(memoryStream, isBaseDescription):
    for memory in memoryStream:
        if isBaseDescription:
            memory["Recency"] = 0
        else:
            currTime = datetime.datetime.utcnow()
            diffInSeconds = (currTime - memory["Creation Time"]).total_seconds()
            minutesDiff = diffInSeconds / 60
            memory["Recency"] = math.exp(-DECAY_FACTOR * minutesDiff)
    return memoryStream


def calculateRelevance(currentConversation: str, observationData: list):
    contentEmbedding = model.encode(currentConversation, convert_to_tensor=True)
    dataEmbedding = model.encode(observationData, convert_to_tensor=True)
    similarityVector = util.pytorch_cos_sim(contentEmbedding, dataEmbedding).tolist()[0]
    return similarityVector


def calculateRetrievalScore(
    observationData: list,
    recencyScores: list,
    similarityVector: list,
    retrievalCount: int,
):
    global currStatement
    global csvData
    relevantObservations = [(float("-inf"), "") for i in range(retrievalCount)]
    heapify(relevantObservations)
    for idx, simScore in enumerate(similarityVector):
        retrievalScore = (
            recencyScores[idx] * RECENCY_WEIGHT + simScore * RELEVANCE_WEIGHT
        )

        currData = {
            "Current Statement": currStatement,
            "Observations": observationData[idx],
            "RecencyScore": recencyScores[idx],
            "RelevancyScore": simScore,
            "TotalScore": retrievalScore,
        }
        currObservation = (retrievalScore, observationData[idx])
        if retrievalScore > relevantObservations[0][0]:
            heappushpop(relevantObservations, currObservation)
        csvData.append(currData)
        updateCSV()
    return sorted(relevantObservations, key=lambda x: x[0], reverse=True)


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
    global csvData
    headers = [
        "Current Statement",
        "Observations",
        "RecencyScore",
        "RelevancyScore",
        "TotalScore",
    ]
    with open(
        f"DF_{DECAY_FACTOR}_RECW_{RECENCY_WEIGHT}_RELW_{RELEVANCE_WEIGHT}_retCount10.csv",
        "w",
        newline="",
    ) as csvFile:
        csvWriter = csv.DictWriter(csvFile, fieldnames=headers)
        csvWriter.writeheader()
        csvWriter.writerows(csvData)
