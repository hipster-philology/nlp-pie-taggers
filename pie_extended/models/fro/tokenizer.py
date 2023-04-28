import regex as re
from typing import List, Generator, Tuple

from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.pipeline.tokenizers.utils.excluder import (
    ExcluderPrototype,
    DottedNumberExcluder,
    ApostropheExcluder,
    ReferenceExcluder,
    CharRegistry
)
from pie_extended.pipeline.tokenizers.utils import regexps
from pie_extended.utils import roman_number

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"
_Dots_collections = r"[" + _Dots_except_apostrophe + "‘’]"


class FroMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    re_remove_ending_apostrophe = re.compile(r"(?<=\w)([\'’ʼ])")
    re_roman_number = re.compile(r"^"+regexps.RomanNumbers+"$")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )

    def __init__(self):
        super(FroMemorizingTokenizer, self).__init__()
        self.tokens = []
        self.char_registry: CharRegistry = CharRegistry()
        self.normalizers: Tuple[ExcluderPrototype, ...] = (
            ApostropheExcluder(char_registry=self.char_registry),
            ReferenceExcluder(char_registry=self.char_registry),
            DottedNumberExcluder(char_registry=self.char_registry),
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
        if lower:
            text = text.lower()
        text = text.split()
        return text

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
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
        if out > 2:
            out = 2
        return str(out)

    def replacer(self, inp: str):
        if self.re_roman_number.match(inp):
            return self.roman_to_number(inp)
        for excluder in self.normalizers:
            if not excluder.can_be_replaced and excluder.exclude_regexp.match(inp):
                return inp
        return self.re_remove_ending_apostrophe.sub("", inp)
