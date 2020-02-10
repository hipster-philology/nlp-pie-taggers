import regex as re
import string

from pie.tagger import simple_tokenizer
from typing import Callable, List, Tuple, Dict, Union, Iterable

from ...pipeline.tokenizers.classes import Tokenizer
from ...utils import ObjectCreator

Remover = Callable[[List[str]], Tuple[List[str], Dict[int, str]]]
PUNKT = re.compile(r"^[_||[^\s\w]]+$", re.VERSION1)


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
