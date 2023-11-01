import spacy
import math

nlp = spacy.load('en_core_web_md')
###
### use the spaCy library which has pre-trained word embeddings built-in.
### The English core model en_core_web_md comes with word vectors included.
###
def cosine_similarity(vec1, vec2):
    dot_product = sum(p * q for p, q in zip(vec1, vec2))
    magnitude = math.sqrt(sum([val ** 2 for val in vec1])) * math.sqrt(sum([val ** 2 for val in vec2]))
    if not magnitude:
        return 0
    return dot_product / magnitude


def calculate_relevance(content, stored_memory_data):
    content_embedding = nlp(content).vector

    similarities = []
    for data in stored_memory_data:
        data_embedding = nlp(data).vector
        similarity = cosine_similarity(content_embedding, data_embedding)
        similarities.append(similarity)

    return similarities




## 2. sentenceTransformer
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


def calculate_relevance_with_sbert(content, stored_memory_data):
    content_embedding = model.encode(content, convert_to_tensor=True)

    similarities = []
    for data in stored_memory_data:
        data_embedding = model.encode(data, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(content_embedding, data_embedding).item()
        similarities.append(similarity)

    return similarities


# Example usage:
content = "Tony is going to watch movie "
stored_memory_data = ["Tony loves watching movie", "Tony ate breakfast bagel in the morning.",
                      "Apples are delicious.", "Tony is 25 year-old", "Tony's father is a firefighter."]

# spaCy library
# sentenceTransformer
print(calculate_relevance(content, stored_memory_data))
print(calculate_relevance_with_sbert(content, stored_memory_data))
