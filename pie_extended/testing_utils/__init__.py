from pie_extended.tagger import ExtensibleTagger


class FakeTagger(ExtensibleTagger):
    def __init__(self, tokens, tasks):
        self.tokens = tokens
        self.tasks = tasks
        self.seen = []
        self.lower = False
        self.batch_size = 100
        self.disambiguation = None

    def tag(self, sents, **kwargs):
        self.seen.extend(sents)

        return self.tokens, self.tasks
