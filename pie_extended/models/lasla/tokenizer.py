import regex as re
from typing import List, Generator

from pie_extended.models.fro.tokenizer import _Dots_except_apostrophe, _RomanNumber
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.models.lasla._params import abbrs


class LatMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    re_abbr_dot = re.compile(
        r"("+r"|".join([abbr.replace(".", "") for abbr in abbrs])+r")(\.)"
    )
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    roman_number_dot = re.compile(r"\.(" + _RomanNumber + r")\.")

    def __init__(self):
        super(LatMemorizingTokenizer, self).__init__()
        self.tokens = []

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    @classmethod
    def _real_sentence_tokenizer(cls, string: str) -> List[str]:
        string = cls._sentence_boundaries.sub(cls._sentence_tokenizer_merge_matches, string)
        string = string.replace("語", ".")
        return string.split("<SPLIT>")

    def _real_word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        if lower:
            text = text.lower()
        return text.split()

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        """

        >>> x = LatMemorizingTokenizer()
        >>> list(x.sentence_tokenizer("Lasciva puella et lasciue Agamemnone whateverve."))
        [['lasciua', 'puella', 'et', 'lasciue', 'agamemnone', 'whateuer', '-ue', '.']]

        """
        sentences = list()
        data = self.normalizer(text)
        for sent in self._real_sentence_tokenizer(data):
            sent = sent.strip()
            if sent:
                sentences.append(self.word_tokenizer(sent))
        yield from sentences

    def _abbr_replace(self, match):
        string, dot = (match.groups())
        return string+'語'

    def normalizer(self, data: str) -> str:
        data = self.re_add_space_around_punct.sub(
            r" \g<2> ",
            self.re_abbr_dot.sub(
                self._abbr_replace,
                self.roman_number_dot.sub(
                    r"語\g<1>語",
                    data
                )
            )
        )
        return data

    def replacer(self, inp: str):
        inp = inp.replace("V", "U").replace("v", "u").replace("J", "I").replace("j", "i").replace(".", "")
        return inp
