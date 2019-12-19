__desc__ = """These are less prototypes than full fledged implementation that should be used as the 
basis for further developments """

from pie.tagger import simple_tokenizer
from typing import Callable, Iterable, List, Tuple, Union, Dict
import string
import re


Tokenizer = Callable[[str, bool], Iterable[List[str]]]

# (sentence) -> List of words, index+reinsertion
# eg. DataIterator.remove_punctuation
Remover = Callable[[List[str]], Tuple[List[str], Dict[int, str]]]


PUNKT = re.compile("^["+string.punctuation+"]+$")


class ObjectCreator:
    """ Some objects should be reset everytime a new tagging is done. To make this easier
    we provide this class that keeps in memory the initialization parameters."""
    def __init__(self, cls, *args, **kwargs):
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def create(self):
        return self.cls(*self.args, **self.kwargs)


class DataIterator:
    def __init__(self, tokenizer: Union[ObjectCreator, Tokenizer] = None, remove_from_input: Callable = None):
        """ Iterator used to parse the text and returns bits to tag

        :param tokenizer: Tokenizer
        """
        self.tokenizer = tokenizer or simple_tokenizer
        self.remove_from_input = remove_from_input
        if self.remove_from_input is None:
            self.remove_from_input = lambda x: (x, {})

    @staticmethod
    def remove_punctuation(sentence: List[str]) -> Tuple[List[str], Dict[int, str]]:
        """ Removes punctuation from a list and keeps its index

        :param sentence:
        :return: First the sentence with things removed, then a dictionary whose keys are index of token to reinsert and
        associated values are punctuation to reinsert.

        >>> x = DataIterator.remove_punctuation(["Je", "suis", "content",",", "mais", "...", '"', "fatigué", '"', "."])
        >>> assert x == (['Je', 'suis', 'content', 'mais', 'fatigué'], {3: ',', 5: '...', 6: '"', 8: '"', 9: '.'})
        """
        clean, removed = [], {}
        for index, token in enumerate(sentence):
            if PUNKT.match(token):
                removed[index] = token
            else:
                clean.append(token)
        return clean, removed

    def get_tokenizer(self) -> Tokenizer:
        """ Get the tokenizer if it needs to be created"""
        if isinstance(self.tokenizer, ObjectCreator):
            return self.tokenizer.create()
        return self.tokenizer

    def get_remover(self) -> Remover:
        if isinstance(self.remove_from_input, ObjectCreator):
            return self.remove_from_input.create()
        return self.remove_from_input

    def __call__(self, data: str, lower: bool = False) -> Iterable[Tuple[List[str], int, Dict[int, str]]]:
        """ Default iter data takes a text, an option to make lower
        and yield lists of words along with the length of the list

        :param data: A plain text
        :param lower: Whether or not to lower the text
        :yields: (Sentence as a list of word, Size of the sentence, Elements removed from the sentence)
        """
        tokenizer = self.get_tokenizer()
        remover = self.get_remover()
        for sentence in tokenizer(data, lower=lower):
            clean_sentence, removed_from_input = remover(sentence)
            yield clean_sentence, len(clean_sentence), removed_from_input


class Formatter:  # Default is TSV
    def __init__(self, tasks: List[str]):
        self.tasks: List[str] = tasks

    def format_line(self, token: str, tags: Iterable[str], ignored=False) -> List[str]:
        """ Format the tags"""
        return [token] + list(tags)

    def write_line(self, formatted):
        return "\t".join(formatted) + "\r\n"

    def write_sentence_beginning(self) -> str:
        return ""

    def write_sentence_end(self) -> str:
        return ""

    def write_footer(self) -> str:
        return ""

    def get_headers(self):
        return ["token"] + self.tasks

    def write_headers(self)-> str:
        """ Format the headers """
        return self.write_line(self.get_headers())


class MemoryzingTokenizer(object):
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

    def __init__(self, sentence_tokenizer=None, word_tokenizer=None, replacer=None):
        self.tokens = [
        ]

        self.sentence_tokenizer = sentence_tokenizer or self._sentence_tokenizer
        self.word_tokenizer = word_tokenizer or self._word_tokenizer
        self.replacer = replacer or self._replacer

    def __call__(self, data, lower=True):
        if lower:
            data = data.lower()

        for sentence in self.sentence_tokenizer(data):
            toks = self.word_tokenizer(sentence)
            new_sentence = []

            for tok in toks:
                out = self.replacer(tok)
                self.tokens.append((len(self.tokens), tok, out))
                new_sentence.append(out)

            yield new_sentence


class Disambiguator:
    """ Function or class that takes a list of words and returns the disambiguated list of words as tuples"""
    def __call__(self, sent, tasks) -> Tuple[List[str], List[Dict[str, str]]]:
        raise NotImplementedError
