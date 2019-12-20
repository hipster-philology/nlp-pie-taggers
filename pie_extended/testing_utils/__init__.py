class FakeTagger:
    def __init__(self, tokens, tasks):
        self.tokens = tokens
        self.tasks = tasks
        self.seen = []

    def tag(self, sents, lengths=0):
        self.seen.extend(sents)

        return self.tokens, self.tasks
