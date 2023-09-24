from heapq import heapify, heappushpop
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
# Recency : not needed mostly...


def retrievalFunction(currentConversation: str, memoryStream: list):
    return calculateRelevance(currentConversation, memoryStream)


def calculateRelevance(currentConversation: str, memoryStream: list):
    contentEmbedding = model.encode(currentConversation, convert_to_tensor=True)
    memoryData = [
        (memory, observation)
        for memory in memoryStream
        for observation in memory["Observations"]
    ]
    observationData = [observation for memory, observation in memoryData]
    dataEmbedding = model.encode(observationData, convert_to_tensor=True)
    similarityVector = util.pytorch_cos_sim(contentEmbedding, dataEmbedding).tolist()[0]
    relevantObservations = [(float("-inf"), "") for i in range(3)]
    heapify(relevantObservations)
    for idx, simScore in enumerate(similarityVector):
        relevance = simScore
        currObservation = (relevance, observationData[idx])
        if relevance > relevantObservations[0][0]:
            heappushpop(relevantObservations, currObservation)

    return sorted(relevantObservations, key=lambda x: x[0], reverse=True)
