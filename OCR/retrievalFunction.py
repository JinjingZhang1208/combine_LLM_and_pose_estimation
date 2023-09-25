from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
# Recency : not needed mostly...

def retrievalFunction(currentConversation:str,memoryStream:list):
    return calculateRelevance(currentConversation,memoryStream)

def calculateRelevance(currentConversation:str, memoryStream:list):
    content_embedding = model.encode(currentConversation, convert_to_tensor=True)
    observationData=[]
    for memory in memoryStream:
        for observation in memory['Observations']:
            data_embedding = model.encode(observation, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(content_embedding, data_embedding).item()
            observationData.append({'observationText':observation,'relevance':similarity})
    mostRelevantData=sorted(observationData,key=lambda x : x['relevance'],reverse=True)
    return mostRelevantData[:5] 

"""
def calculateImportance(content,stored_memory_data):
    importancePrompt ={
        "context": f"You are a conversational agent who will is provided with a set of observation strings. Determine the most important observations based on the current conversation.",
        "information": {
            "description":"Provide an integer on a scale of 1 to 10 where 1 is purely mundane and 10 is extremely poigant. rate the likely poigancy of the following observation strings"
        }
    }




def createBasePrompt(userName,baseDescription):

    BACKGROUND_DESCRIPTION_CONTEXT=f"You are the user {userName}. You wil be provided with a description with background details about you."

    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": BACKGROUND_DESCRIPTION_CONTEXT,
        "information": {
            "description":baseDescription
        },
        "criteria": [
            "Generate a list consisting of all the important observations made from the description",
            "Each item in the list should consist of one observation separated by a new line"
        ],
        "example": "(Observation 1)\n(Observation 2)\n"
    }
    return json.dumps(prompt,indent=4)
"""


