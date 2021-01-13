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
    def __init__(self, tokenizer: SimpleTokenizer = None, exclude_patterns: List[Union[str, Pattern]] = None,
                 max_tokens: int = 256):
        """ Iterator used to parse the text and returns bits to tag

        :param tokenizer: Tokenizer
        """
        self.tokenizer: SimpleTokenizer = tokenizer or SimpleTokenizer()
        self.exclude_patterns: List[Pattern] = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                self.add_pattern(pattern)
        self.max_tokens = max_tokens

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

    def _max_out(self, sentences):
        for sentence in sentences:
            if len(sentence) <= self.max_tokens:
                yield sentence
            else:
                for n in range(0, len(sentence), self.max_tokens):
                    yield sentence[n:n+self.max_tokens]

    def __call__(self, data: str, lower: bool = False,
                 no_tokenizer: bool = False) -> Iterable[Tuple[List[str], int, Dict[int, str]]]:
        """ Default iter data takes a text, an option to make lower
        and yield lists of words along with the length of the list

        :param data: A plain text
        :param lower: Whether or not to lower the text
        :yields: (Sentence as a list of word, Size of the sentence, Elements removed from the sentence)
        """
        sentences = []

        func = self.tokenizer.sentence_tokenizer
        if no_tokenizer:
            func = self.tokenizer.bypass_tokenizer

        last_sentence_index = 0
        for sentence in self._max_out(func(data, lower=lower)):
            clean_sentence, removed_from_input = self.exclude_tokens(sentence)
            if len(clean_sentence) == 0 and len(sentences):
                sentences[-1][2].update({
                    last_sentence_index + removed_index: removed_value
                    for removed_index, removed_value in removed_from_input.items()
                })
                last_sentence_index += len(removed_from_input)
            else:
                sentences.append((clean_sentence, len(clean_sentence), removed_from_input))
                last_sentence_index = len(sentence)
        yield from sentences
