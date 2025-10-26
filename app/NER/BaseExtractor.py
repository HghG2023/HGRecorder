class BaseExtractor:
    name = "base"

    def extract(self, text: str):
        raise NotImplementedError

