from transformers import pipeline
import torch
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

GPT4='gpt-4'
GPT35='gpt-3.5-turbo'
API_KEY=os.environ.get('API_KEY')
openai.api_key="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"

def predict(input_text):
    model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
    bit_length = 32  # can be 32 = 32 float, 16 = 16 float or 8 = 8 int
    device = "CPU"  # can be "CUDA" or "CPU"

    precision = torch.float32
    if bit_length == 16:  # 16 bit float
        precision = torch.float16
    elif bit_length == 8:  # 8 bit int
        precision = torch.int8

    model = pipeline("text-classification", model=model_name, top_k=None,
                     device=device.lower(),
                     torch_dtype=precision)

    prediction = model(input_text)
    sorted_predictions = sorted(prediction[0], key=lambda x: x['score'], reverse=True)
    return sorted_predictions

def generatePrompt(predictions):
    prompt={
        "context": f"Help user choose one of the most suitable expression for Input from Facial Expression or Body Expression(Emotes) as output. Only give one answer, no reason.",
        "information": {
            "Input":predictions,
        "Facial Expression": {
            "Happy": 2,
            "Smug": 5,
            "Wink": 4,
            "Confused": 3,
            "Excited": 6,
            "Angry": 1
        },
        "Body Expression (Emotes)": {
            "Wave Hands": 1,
            "Clap": 2,
            "Point": 3,
            "Cheer": 4,
            "Dance": 5,
            "Backflip": 6,
            "Sadness": 7,
            "Faint": 8
    }
        },
        "criteria": [
            "Follow human real emotions. Only give a correct choice with no reason. For example, happy.",
        ],
    }
    conversationPrompt=json.dumps(prompt,indent=4)
    return getGPTResponse(conversationPrompt,GPT4)

def getGPTResponse(prompt,gptModel):
    response = openai.ChatCompletion.create(
    model=gptModel,
    messages=[
            {"role": "system", "content": "Help user choose one of the most suitable expressions."},
            {"role": "user", "content": prompt},
        ]
        ,
        temperature=1.0,
    max_tokens=300
    )
    return response['choices'][0]['message']['content']

