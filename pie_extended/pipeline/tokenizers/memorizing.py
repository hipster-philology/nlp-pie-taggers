class MemorizingTokenizer(object):
    """ Tokenizer that memoryze what it tokenized.

    Mostly used to normalized input as input time and then reinserting normalized input

    """
    @staticmethod
    def _sentence_tokenizer(string):
        for s in string.split("."):
            if s.strip():
                yield s.strip() + " " + "."

    @staticmethod
    def _word_tokenizer(string):
        for s in string.split():
            if s.strip:
                yield s.strip()

    @staticmethod
    def _replacer(inp: str):
        return inp

    def __init__(self, sentence_tokenizer=None, word_tokenizer=None, replacer=None, normalizer=None):
        self.tokens = [
        ]

        self.sentence_tokenizer = sentence_tokenizer or self._sentence_tokenizer
        self.word_tokenizer = word_tokenizer or self._word_tokenizer
        self.replacer = replacer or self._replacer
        self.normalizer = normalizer or self._replacer

    def __call__(self, data, lower=True):
        if lower:
            data = data.lower()
        for sentence in self.sentence_tokenizer(data):
            toks = self.word_tokenizer(sentence)
            new_sentence = []

            for tok in toks:
                if tok:
                    out = self.replacer(tok)
                    self.tokens.append((len(self.tokens), tok, out))
                    new_sentence.append(out)
            if new_sentence:
                yield new_sentence
