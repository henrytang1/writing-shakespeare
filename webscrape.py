import random
import re
import requests
from bs4 import BeautifulSoup, Tag
import math
import os.path

N = 4 # N-gram model
totalSentences = 10 # Number of sentences generated

# Used for calculating perplexity
totalElements = 0
logProbability = 0.0

# <s> is used to indicate the start of a string
startString = ""
for i in range(N-1):
    startString += "<s> "
startString = startString.strip()

# Generates ngrams from tokens/items
# items is a list of tokens, N is the size of the ngram
# returns grams, the list of ngrams
def generateNGrams(items, N):
    grams = []
    i = 0
    while i < len(items)-N+1:
        grams.append(items[i:i+N])
        if items[i+N-1] == ".":
            i += N
        else:
            i += 1
    return grams

# Generates frequencies/counts given a list of ngrams
# returns counts, a dictionary of dictionaries. Each key is an input sequence, and the values are all possible outputs with their frequencies
def getFrequencies(ngrams):
    counts = {}

    for ngram in ngrams:
        sequence  = " ".join(ngram[:-1])
        lastItem = ngram[-1]

        if sequence not in counts:
            counts[sequence] = {}

        if lastItem not in counts[sequence]:
            counts[sequence][lastItem] = 0

        counts[sequence][lastItem] += 1

    return counts

# Gets the next word given the current text.
# text is the current string, N is the size of the ngram, and counts is the list of dictionary that corresponds input sequences with output sequences
# returns choice, the next generated word in the sentence
def getNextWord(text, N, counts):
    if N == 1:
        choices = counts[""].items()
    else:
        sequence = " ".join(text.split()[-(N-1):])
        choices = counts[sequence].items()

    total = sum(weight for choice, weight in choices)
    r = random.uniform(0, total)
    upto = 0
    
    for choice, weight in choices:
        upto += weight
        if upto > r:
            global totalElements
            global logProbability
            logProbability += math.log(weight/total) # use log to avoid underflow/overflow
            totalElements += 1
            return choice
    assert False

# Processes input text, where html tags have already been removed
# Returns processed text
def processText(text):
    # Gets rid of newlines, spaces, and brackets
    text = text.replace("\n", " ").replace("\r", "")
    text = re.sub("[\(\[].*?[\)\]]", "", text)
    text = re.sub("\s+"," ",text)
    text = text.strip()
    
    # Lowercases words and more processing
    text = re.sub("[()]", r'', text)
    text = re.sub("([.-])+", r"\1", text)
    text = re.sub("([^0-9])([.,!?])([^0-9])", r"\1 \2 \3", text)
    text = " ".join(text.split()).lower()
    text = re.sub("(\\s+[^a-zA-Z0-9.,!?]\\s+)", "", text)
    text = re.sub("\s+"," ",text)
    
    # Inserts start characters to the start of sentences
    text = insertToString(text, 0, "%s " % startString)
    text = re.sub("([.!?]\\s+)", "\\1%s " % startString, text)
#    print(s)
    return text

# Corrects the appearance of generated sentence
# Returns corrected sentence
def processOutput(sentence):
    sentence = re.sub("<s>", "", sentence)
    sentence = re.sub("\s{2,}", " ", sentence)
    sentence = sentence.strip()
    sentence = re.sub("\\s+([.,!?])\\s*", r"\1 ", sentence)
    sentence = sentence.capitalize()
    sentence = re.sub("([.!?]\\s+[a-z])", lambda c: c.group(1).upper(), sentence)
    sentence = re.sub("( [b-z] )", lambda c: c.group(1).upper(), sentence)
    return sentence

# Generates new sentences from the string trainingText
# Returns newly created sentences in the same style as trainingText
def generateSentence(trainingText):
    ngrams = generateNGrams(trainingText.split(" "), N)
    counts = getFrequencies(ngrams)

    createdText = "%s" % startString

    sentenceIdx = 0
    while sentenceIdx < totalSentences:
        createdText += " " + getNextWord(createdText, N, counts)
        if createdText.endswith((".", "!", "?")):
            sentenceIdx += 1
            createdText += " %s" % startString
    return processOutput(createdText)

# Helper function to add elements to strings
# Adds replacement at index in string
# Returns updated string
def insertToString(string, index, replacement):
    return string[:index] + replacement + string[index:]

# Gets data from url
# Returns a string with html tags removed
def getFromURL(url):
    res = requests.get(url)
    htmlPage = res.content
    soup = BeautifulSoup(htmlPage, "html.parser")

    elements = soup.find_all("a", href="/Shakespeare")
    for element in elements:
        element.decompose()

    elements = soup.find_all("a", href="/Shakespeare/allswell")
    for element in elements:
        element.decompose()

    elements = soup.find_all("td")
    for element in elements:
        element.decompose()

    text = soup.find_all(text=True)

    output = ""
    blacklist = [
        "[document]",
        "noscript",
        "header",
        "html",
        "meta",
        "head",
        "input",
        "script",
        "i",
        "b",
        "title",
        "h3",
        "td",
    ]

    for t in text:
        if t.parent.name not in blacklist:
            output += "{}".format(t)
    
    output.replace("EPILOGUE", "")
    return output

# MAIN

text = ""

if os.path.isfile("textData.txt"):
    f = open("textData.txt", "r")
    text = f.read()
    f.close()
    
else:
    # Gets urls from urls.txt
    f = open("urls.txt", "r")
    urls = [line.strip() for line in f]
    f.close()

    text = ""
    for url in urls:
        text = text + getFromURL(url) + "\n"
    
    f = open("textData.txt", "w")
    f.write(text)
    f.close()
    
# Process data
text = processText(text)

# Generated sentence
print(generateSentence(text))

# Complextiy
print("Perplexity: %f" % math.exp(-logProbability/totalElements))
