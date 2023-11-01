import re
from collections import Counter
import time
# This model is based on the concept of edit distance,
# specifically the Damerau-Levenshtein distance,
# which calculates the number of operations (insertions, deletions, substitutions, and transpositions) needed to transform one string into another.

def words(text): return re.findall(r'\w+', text.lower())


# Here's an extended example corpus.
CORPUS = "This is a sample corpus with some sample sentences and words. How are you? What do you mean by that?"
WORD_COUNTS = Counter(words(CORPUS))


def edits1(word):
    "All edits that are one edit away from `word`."
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def known(words): return set(w for w in words if w in WORD_COUNTS)


def autocorrect_word(word):
    # If the word is already in the corpus, return it as is.
    if word in WORD_COUNTS:
        return word

    # Then, get the list of known words that are one edit away
    candidates = known(edits1(word)) or [word]

    # Return the word with the highest frequency in the corpus
    return max(candidates, key=WORD_COUNTS.get)


def autocorrect_sentence(sentence):
    words_in_sentence = sentence.split()
    corrected_words = [autocorrect_word(word) for word in words_in_sentence]
    return ' '.join(corrected_words)
start_time = time.time()  # get the current time
print("re function"+" :"+autocorrect_sentence('hos are you'))
end_time = time.time()  # get the current time after your code has finished running

elapsed_time = end_time - start_time  # calculate the difference
print(f"Code executed in {elapsed_time:.2f} seconds")


start_time = time.time()  # get the current time
print("re function"+" :"+autocorrect_sentence('whot di you mean'))
end_time = time.time()  # get the current time after your code has finished running
elapsed_time = end_time - start_time  # calculate the difference
print(f"Code executed in {elapsed_time:.2f} seconds")

#It can handle basic mistakes in sentences,
# but for more context-aware corrections,
# a more advanced model or library might be necessary.

import spacy
# Test the autocorrect with spaCy
start_time = time.time()  # get the current time
# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

# Some utility functions
def get_best_match(token):
    # This function finds the most similar word in the vocabulary to the given token
    queries = [w for w in token.vocab if w.is_lower == token.is_lower and w.prob >= -15 and w.has_vector]
    by_similarity = sorted(queries, key=lambda w: token.similarity(w), reverse=True)
    return by_similarity[0].text if by_similarity else token.text

def autocorrect_spacy(sentence):
    doc = nlp(sentence)
    corrected_words = []

    for token in doc:
        # If token is not a stop word, try to autocorrect it
        if not token.is_stop:
            corrected_words.append(get_best_match(token))
        else:
            corrected_words.append(token.text)

    return ' '.join(corrected_words)

print("spacy function"+" :"+autocorrect_spacy('how are you'))
end_time = time.time()  # get the current time after your code has finished running
elapsed_time = end_time - start_time  # calculate the difference
print(f"Code executed in {elapsed_time:.2f} seconds")

from symspellpy import SymSpell, Verbosity
dictionary_text = """
This is a sample corpus with some sample sentences and words.
How are you?
What do you mean by that?
"""
# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

# Create a dictionary from our sample corpus
words = dictionary_text.split()
for word in words:
    sym_spell.create_dictionary_entry(word, 1)  # Assuming each word has a frequency count of 1

# Auto-Correct Function
def autocorrect_symspell(input_term):
    # max edit distance per lookup (per single word, not per whole input string)
    suggestions = sym_spell.lookup(input_term, Verbosity.CLOSEST, max_edit_distance=2)
    # return the best suggestion
    return suggestions[0].term if suggestions else input_term

def autocorrect_sentence_symspell(sentence):
    words = sentence.split()
    corrected_words = [autocorrect_symspell(word) for word in words]
    return ' '.join(corrected_words)

# Test the Auto-Correct
start_time = time.time()  # get the current time
print("symspelly"+" :"+autocorrect_sentence_symspell('whot di you mean'))  # It should return 'what do you mean'
end_time = time.time()  # get the current time after your code has finished running
elapsed_time = end_time - start_time  # calculate the difference
print(f"Code executed in {elapsed_time:.2f} seconds")

from spellchecker import SpellChecker

spell = SpellChecker()

# Detect potentially misspelled words
sentence = "let's hve somm fun"
misspelled = spell.unknown(sentence.split())

for word in misspelled:
    # Get the one `most likely` answer
    print(f"Correct spelling for {word} might be: {spell.correction(word)}")

    # Get a list of `likely` options
    print(f"Suggestions for {word} are: {spell.candidates(word)}")