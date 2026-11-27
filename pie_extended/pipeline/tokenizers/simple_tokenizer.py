from typing import Generator, List, Optional
import regex as re
import string
from pie.tagger import regexsplitter, SECTION, FULLSTOP

WORD = r'([{}])'.format(string.punctuation)

RE_BYPASS_SENTENCE = re.compile(r"(?:\r?\n){2,}")
RE_BYPASS_WORD = re.compile(r"(?:\r?\n)")


class SimpleTokenizer(object):
    """ Tokenizer that memoryze what it tokenized.

    Mostly used to normalized input as input time and then reinserting normalized input

    """
    def __init__(self):
        self.section = regexsplitter(SECTION)
        self.fullstop = regexsplitter(FULLSTOP)
        self.word = regexsplitter(WORD)

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        for line in self.section(text):
            for sentence in self.fullstop(line):
                yield self.word_tokenizer(sentence, lower=lower)

    def word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        sentence = [w for raw in text.split() for w in self.word(raw)]
        if lower:
            sentence = [w.lower() for w in sentence]
        return sentence

    def reset(self):
        """Can be used between documents for example """
        pass

    def surface_tokens(self) -> Optional[List[str]]:
        """ How each token of the last text read is written in this text, if it differs from the token itself.

        None (the default) means that tokens are written as they are (or, for memorizing tokenizers, that
        their memory knows it). A tokenizer that moves things around (see the Armenian one) overrides it to give,
        for each token, the part of the text it comes from, or an empty string for a token that is written nowhere.
        """
        return None

    def bypass_tokenizer(self, data: str, lower: bool = False) -> Generator[List[str], None, None]:
        """ Function to enable pretokenized input while using replaces or the likes

        :param data: The string (one new line = one word, two new lines = two words)
        :param lower: Whether to lower the input


        >>> tokenizer = SimpleTokenizer()
        >>> list(tokenizer.bypass_tokenizer("one\\ntwo\\nthree\\n\\n.//.\\na\\nz"))
        [['one', 'two', 'three'], ['.//.', 'a', 'z']]
        """

        for sentence in RE_BYPASS_SENTENCE.split(data):
            if sentence:
                yield [word for word in RE_BYPASS_WORD.split(sentence) if word]


class LengthTokenizer(SimpleTokenizer):
    def __init__(self, max_len=35):
        super(LengthTokenizer, self).__init__()
        self.max_len = max_len

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        sentence = []
        for token in text.split():
            sentence.append(token)
            if len(sentence) == self.max_len:
                yield sentence
                sentence = []
        if sentence:
            yield sentence

    def word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        if lower:
            return text.lower().split()
        return text.split()