import regex as re
from typing import List, Generator, Tuple
import unicodedata

from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.pipeline.tokenizers.utils.excluder import (
    ReferenceExcluder,
    ExcluderPrototype,
    DEFAULT_CHAR_REGISTRY
)

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"


class GrcMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )

    def __init__(self):
        super(GrcMemorizingTokenizer, self).__init__()
        self.tokens = []
        self.char_registry = DEFAULT_CHAR_REGISTRY
        self.normalizers: Tuple[ExcluderPrototype, ...] = (
            ReferenceExcluder(char_registry=self.char_registry),
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

    def replacer(self, inp: str):
        for excluder in self.normalizers:
            if not excluder.can_be_replaced and excluder.exclude_regexp.match(inp):
                return inp

        return unicodedata.normalize("NFKD", inp)
