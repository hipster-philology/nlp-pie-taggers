from .simple_tokenizer import SimpleTokenizer
from typing import List, Tuple, Dict


class MemorizingTokenizer(SimpleTokenizer):
    """ Tokenizer that memoryze what it tokenized.

    Mostly used to normalized input as input time and then reinserting normalized input

    """

    def replacer(self, token: str) -> str:
        """ This function allows for changing input and keeping it in memory """
        return token

    def __init__(self):
        self.tokens: List[Tuple[int, str, str]] = []

    def _real_word_tokenizer(self, data: str, lower: bool = False) -> List[str]:
        return super(MemorizingTokenizer, self).word_tokenizer(data, lower=lower)

    def word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        sentence = []
        for token in self._real_word_tokenizer(text, lower):
            out = self.replacer(token)
            self.tokens.append((len(self.tokens), token, out))
            sentence.append(out)
        return sentence

    def reset(self):  # Empty
        self.tokens = []

