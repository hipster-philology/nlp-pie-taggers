from .simple_tokenizer import SimpleTokenizer, RE_BYPASS_SENTENCE, RE_BYPASS_WORD
from typing import List, Tuple, Generator


class MemorizingTokenizer(SimpleTokenizer):
    """ Tokenizer that memoryze what it tokenized.

    Mostly used to normalized input as input time and then reinserting normalized input

    """

    def replacer(self, token: str) -> str:
        """ This function allows for changing input and keeping it in memory """
        return token

    def __init__(self):
        self.tokens = []

    @property
    def tokens(self) -> List[Tuple[int, str, str]]:
        """ Memory of the tokenizer: (Index, Original input, Input seen by the tagger) for each token.

        Replacing it (what `reset` does) also rewinds the cursor used by `next_token`.
        """
        return self._tokens

    @tokens.setter
    def tokens(self, value: List[Tuple[int, str, str]]) -> None:
        self._tokens = value
        self._cursor = 0

    def next_token(self) -> Tuple[int, str, str]:
        """ Gives the next entry of the memory, in the order of the text (O(1), unlike `list.pop(0)`)

        >>> tokenizer = MemorizingTokenizer()
        >>> tokenizer.tokens = [(0, "A", "a"), (1, "b", "b")]
        >>> tokenizer.next_token(), tokenizer.next_token()
        ((0, 'A', 'a'), (1, 'b', 'b'))
        >>> tokenizer.next_token()
        Traceback (most recent call last):
        ...
        IndexError: The memory of the tokenizer has no more tokens
        >>> tokenizer.reset()
        >>> tokenizer.tokens
        []
        """
        if self._cursor >= len(self._tokens):
            raise IndexError("The memory of the tokenizer has no more tokens")
        entry = self._tokens[self._cursor]
        self._cursor += 1
        return entry

    def _real_word_tokenizer(self, data: str, lower: bool = False) -> List[str]:
        return super(MemorizingTokenizer, self).word_tokenizer(data, lower=lower)

    def _word_logic(self, token: str) -> str:
        out = self.replacer(token)
        self.tokens.append((len(self.tokens), token, out))
        return out

    def word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        sentence = []
        for token in self._real_word_tokenizer(text, lower):
            sentence.append(self._word_logic(token))
        return sentence

    def reset(self):  # Empty
        self.tokens = []

    def bypass_tokenizer(self, data: str, lower: bool = False) -> Generator[List[str], None, None]:
        """ Function to enable pretokenized input while using replaces or the likes

       :param data: The string (one new line = one word, two new lines = two words)
       :param lower: Whether to lower the input


       >>> tokenizer = MemorizingTokenizer()
       >>> list(tokenizer.bypass_tokenizer("One\\ntwo\\nthree\\n\\n.//.\\na\\nz"))
       [['One', 'two', 'three'], ['.//.', 'a', 'z']]
       >>> tokenizer.tokens
       [(0, 'One', 'One'), (1, 'two', 'two'), (2, 'three', 'three'), (3, './/.', './/.'), (4, 'a', 'a'), (5, 'z', 'z')]

       """
        for sentence in RE_BYPASS_SENTENCE.split(data):
            if sentence:
                yield [self._word_logic(word) for word in RE_BYPASS_WORD.split(sentence)]



