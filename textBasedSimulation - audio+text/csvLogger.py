import csv
import os
from enum import Enum
from datetime import datetime


class LogElements(Enum):
    MESSAGE = "Message"
    IMPORTANT_OBSERVATIONS = "Important Observations"
    IMPORTANT_SCORES = "Important Scores"
    NPC_RESPONSE = "NPC Response"
    TIME_FOR_INPUT = "Time for Input"
    TIME_AUDIO_TO_TEXT = "Time for Audio to Text"
    TIME_RETRIEVAL = "Time for Retrieval"
    TIME_FOR_RESPONSE = "Time for Response"
    TIME_FOR_CONTROLEXP = "Time for Expression"
    TIME_FOR_TTS = "Time for TextToSpeech"


class CSVLogger:
    enum_values = {}
    initialize_header = True
    curr_time = datetime.now(tz=None)
    curr_time = curr_time.strftime("%Y-%m-%d_%H-%M")
    curr_file = f"CSV_LOGS_{curr_time}.csv"

    def set_enum(self, enum: Enum, result):
        self.enum_values[enum.value] = result

    def write_to_csv(self, log_values=True):
        headers = [header.value for header in LogElements]
        if log_values:
            with open(self.curr_file, "a", newline="", encoding="utf-8") as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
                if self.initialize_header:
                    csv_writer.writeheader()
                    self.initialize_header = False
                csv_writer.writerow(self.enum_values)
