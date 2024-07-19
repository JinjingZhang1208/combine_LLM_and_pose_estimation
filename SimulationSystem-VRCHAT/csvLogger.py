import csv
import os
from enum import Enum
from datetime import datetime

class LogElements(Enum):
    MESSAGE = "Message"
    IMPORTANT_OBSERVATIONS = "Important Observations"
    IMPORTANT_SCORES = "Important Scores"
    NPC_RESPONSE = "NPC Response"
    TIME_FOR_INPUT = "Total time for Input"
    TIME_FOR_HUMAN_SPEECH_RECOGNITION = "Time for Human speech detection"
    TIME_FOR_VOICE_NORMALIZATION = "Time for voice normalization"
    TIME_FOR_AUDIO_RECORD = "Time for audio recording"
    TIME_AUDIO_TO_TEXT = "Time for Audio to Text"
    TIME_RETRIEVAL = "Time for Retrieval"
    TIME_FOR_RESPONSE = "Time for Response"
    TIME_FOR_REFLECTION = "Time for Reflection"
    TIME_FOR_GENERATE_OBS = "Time for Generate Observations"

class CSVLogger:
    def __init__(self):
        self.enum_values = {}
        self.initialize_header = True
        curr_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.curr_file = f"evaluations/TestScenarios_CSV/CSV_LOGS_{curr_time}.csv"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.curr_file), exist_ok=True)

    def set_enum(self, enum: Enum, result):
        self.enum_values[enum.value] = result

    def write_to_csv(self, log_values=True):
        headers = [header.value for header in LogElements]
        if log_values:
            try:
                with open(self.curr_file, "a", newline="", encoding="utf-8") as csv_file:
                    csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
                    if self.initialize_header:
                        csv_writer.writeheader()
                        self.initialize_header = False
                    csv_writer.writerow(self.enum_values)
            except Exception as e:
                print(f"Error writing to CSV: {e}")
