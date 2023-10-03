from transformers import pipeline
import torch


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


# Example Usage
text = "I love you"
predictions = predict(text)
print(predictions)
