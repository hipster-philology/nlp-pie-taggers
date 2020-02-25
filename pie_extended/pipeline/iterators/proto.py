import regex as re

from typing import List, Tuple, Dict, Iterable, Pattern, Union

from pie_extended.pipeline.tokenizers.simple_tokenizer import SimpleTokenizer
from enum import Enum


class GenericExcludePatterns(Enum):
    """ Useful set of regular expresion that can be used for the exclude_patterns

    """
    Punctuation_and_Underscore: Pattern = re.compile(r"^[_||[^\s\w]]+$", re.VERSION1)
    Punctuation: Pattern = re.compile(r"^[^\s\w]+$")
    PassageMarker: Pattern = re.compile(r"_Passage_[\w\d_]+")  # Use `_` as a joining character


class DataIterator:
    def __init__(self, tokenizer: SimpleTokenizer = None, exclude_patterns: List[Union[str, Pattern]] = None):
        """ Iterator used to parse the text and returns bits to tag

        :param tokenizer: Tokenizer
        """
        self.tokenizer: SimpleTokenizer = tokenizer or SimpleTokenizer()
        self.exclude_patterns: List[Pattern] = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                self.add_pattern(pattern)

    def add_pattern(self, pattern: str):
        """ Add a pattern for removal

        :param pattern: Pattern for token removal
        """
        if isinstance(pattern, str):
            self.exclude_patterns.append(re.compile(pattern))
        elif hasattr(pattern, "value"):  # Deal with enum
            self.exclude_patterns.append(pattern.value)
        else:
            self.exclude_patterns.append(pattern)

    def reset_patterns(self) -> None:
        """ Removes removal patterns

        >>> x = DataIterator(exclude_patterns=[r'\W+'])
        >>> x.exclude_tokens(["Je", "suis", "content", ",", "mais", "...", '"', "fatigué", '"', "."])
        (['Je', 'suis', 'content', 'mais', 'fatigué'], {3: ',', 5: '...', 6: '"', 8: '"', 9: '.'})
        >>> x.reset_patterns()
        >>> x.exclude_tokens(["Je", "suis", "content", ",", "mais", "...", '"', "fatigué", '"', "."])
        (['Je', 'suis', 'content', ',', 'mais', '...', '"', 'fatigué', '"', '.'], {})
        """
        self.exclude_patterns = []

    def exclude_tokens(self, sentence: List[str]) -> Tuple[List[str], Dict[int, str]]:
        """ Removes punctuation from a list and keeps its index

        :param sentence:
        :return: First the sentence with things removed, then a dictionary whose keys are index of token to reinsert and
        associated values are punctuation to reinsert.

        You can use string when generating the exclude_pattern

        >>> x = DataIterator(exclude_patterns=[r'\W+'])
        >>> x.exclude_tokens(["Je", "suis", "content",",", "mais", "...", '"', "fatigué", '"', "."])
        (['Je', 'suis', 'content', 'mais', 'fatigué'], {3: ',', 5: '...', 6: '"', 8: '"', 9: '.'})

        Pre-built removers:

        >>> x = DataIterator(exclude_patterns=[GenericExcludePatterns.PassageMarker])
        >>> x.exclude_tokens(["_Passage_45_78", "Ici", "commence", "le", "passage"])
        (['Ici', 'commence', 'le', 'passage'], {0: '_Passage_45_78'})

        And of course you can ignore this option

        >>> x = DataIterator()
        >>> x.exclude_tokens(["_Passage_45_78", "Ici", "commence", "le", "passage"])
        (['_Passage_45_78', 'Ici', 'commence', 'le', 'passage'], {})

        """
        if len(self.exclude_patterns) == 0:
            return sentence, {}

        clean, removed = [], {}
        for index, token in enumerate(sentence):
            match = False
            for exclude_pattern in self.exclude_patterns:
                if exclude_pattern.match(token):
                    removed[index] = token
                    match = True
                    break
            if not match:
                clean.append(token)

        return clean, removed

    def __call__(self, data: str, lower: bool = False) -> Iterable[Tuple[List[str], int, Dict[int, str]]]:
        """ Default iter data takes a text, an option to make lower
        and yield lists of words along with the length of the list

        :param data: A plain text
        :param lower: Whether or not to lower the text
        :yields: (Sentence as a list of word, Size of the sentence, Elements removed from the sentence)
        """
        for sentence in self.tokenizer.sentence_tokenizer(data, lower=lower):
            clean_sentence, removed_from_input = self.exclude_tokens(sentence)
            yield clean_sentence, len(clean_sentence), removed_from_input
