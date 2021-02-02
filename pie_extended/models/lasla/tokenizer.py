import regex as re
from typing import List, Generator, Tuple
from unidecode import unidecode

from pie_extended.models.fro.tokenizer import _Dots_except_apostrophe
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.models.lasla._params import abbrs
from pie_extended.pipeline.tokenizers.utils.excluder import (
    ReferenceExcluder,
    ExcluderPrototype,
    RegexpExcluder,
    AbbreviationsRemoverExcluder,
    DEFAULT_CHAR_REGISTRY
)
from pie_extended.pipeline.tokenizers.utils import regexps
from pie_extended.utils import roman_number


class LatMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    re_words = re.compile("^\w+$")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    re_roman_number = re.compile(r"^"+regexps.RomanNumbers+"$")

    def __init__(self):
        super(LatMemorizingTokenizer, self).__init__()
        self.tokens = []
        self.char_registry = DEFAULT_CHAR_REGISTRY
        self.normalizers: Tuple[ExcluderPrototype, ...] = (
            ReferenceExcluder(char_registry=self.char_registry),
            ReferenceExcluder(regex_string=r"(\[IGN:[^\]]+\])", char_registry=self.char_registry),
            RegexpExcluder(r"(\p{Greek}+)"),
            RegexpExcluder(r"(\p{No})"),
            AbbreviationsRemoverExcluder(abbrs=abbrs, char_registry=self.char_registry)
        )

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    def _real_sentence_tokenizer(self, string: str) -> List[str]:
        string = self._sentence_boundaries.sub(self._sentence_tokenizer_merge_matches, string)

        for normalizer in self.normalizers:
            string = normalizer.after_sentence_tokenizer(string)

        return string.split("<SPLIT>")

    def _real_word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        if lower is True:
            text = text.lower()
        return text.split()

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        """

        >>> x = LatMemorizingTokenizer()
        >>> list(x.sentence_tokenizer("XX Lasciva puella et lasciue C. Agamemnone whateverve."))
        [['3', 'Lasciua', 'puella', 'et', 'lasciue', 'C', 'Agamemnone', 'whateuerue', '.']]

        """
        sentences = list()
        data = self.normalizer(text)
        for sent in self._real_sentence_tokenizer(data):
            sent = sent.strip()
            if sent:
                sentences.append(self.word_tokenizer(sent))
        yield from sentences

    def normalizer(self, data: str) -> str:
        for excluder in self.normalizers:
            data = excluder.before_sentence_tokenizer(data)

        data = self.re_add_space_around_punct.sub(
            r" \g<2> ",
            data
        )
        return data

    def roman_to_number(self, inp: str) -> str:
        out = roman_number(inp)
        if out > 3:
            out = 3
        return str(out)

    def replacer(self, inp: str):
        """

        :param inp:
        :return:

        """
        for excluder in self.normalizers:
            if not excluder.can_be_replaced and excluder.exclude_regexp.match(inp):
                return inp
        if self.re_roman_number.match(inp):
            return self.roman_to_number(inp)
        elif inp.isnumeric():
            if inp.isdigit():  # avoid. ↀ
                if int(inp) > 3:
                    return "3"
                else:
                    return inp
            return "3"
        elif "." == inp:
            return "."

        if self.re_words.match(inp):  # Might check somehow else but for now... It's weird unidecode normalize into SS
            inp = unidecode(inp)
        inp = inp.replace("V", "U").replace("v", "u").replace("J", "I").replace("j", "i").replace(".", "")#.lower()
        return inp
