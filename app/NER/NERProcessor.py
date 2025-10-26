from scripts.Tools import r
from .BaseExtractor import BaseExtractor
from .DateExtractor import DateExtractor
from .DurationExtractor import DurationExtractor
from .EventExtractor import EventExtractor
from .PersonExtractor import PersonExtractor
from .PlaceExtractor import PlaceExtractor
from .RecurrenceExtractor import RecurrenceExtractor
from .TimeExtractor import TimeExtractor
from .WeekExtractor import WeekExtractor

class NERProcessor:
    def __init__(self):
        self.extractors = [
            DateExtractor(),
            TimeExtractor(),
            WeekExtractor(),
            PlaceExtractor(),
            PersonExtractor(),
            EventExtractor(),
            DurationExtractor(),
            RecurrenceExtractor(),
        ]

    def process_text(self, text_path: str):
        text = r(text_path).replace("\n", "").replace("\u2005", " ").strip()

        results = {}
        for extractor in self.extractors:
            values = extractor.extract(text)
            results[extractor.name] = values if values else None

        results["events_full"] = text
        return {"ner_extract": results}
    
