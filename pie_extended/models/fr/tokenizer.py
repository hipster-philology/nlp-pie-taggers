import regex as re
from typing import List, Generator, Tuple

from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.pipeline.tokenizers.utils import regexps, chars
from pie_extended.pipeline.tokenizers.utils.excluder import (
    ExcluderPrototype, CompoundAbbreviationsExcluder, ApostropheExcluder,
    ReferenceExcluder,
    CharRegistry
)
from pie_extended.models.fr.excluders import FrenchCliticsExcluder, ABBREVIATIONS, AujourdhuiExcluder

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"


""" This code has been removed for now, might be reused later

    # ToDo: Transform into Agglutinated excluder ?
    _data_re_keep_together = "peut-être, peut-estre, sur-tout, long-temps, par-tout, vis-à-vis".split(", ")
    re_keep_together = re.compile(
        r"("+"|".join([
            token
            for token in _data_re_keep_together
        ])+r")(?:\b|$)",
        flags=re.IGNORECASE
    )

    def replace_keep_together(self, regex_match) -> str:
        return regex_match.group(0).replace("-", "分")
"""


class FrMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(regexps.NON_WORD_NON_SPACE)
    re_remove_ending_apostrophe = re.compile(regexps.ENDING_APOSTROPHE)
    re_sentence_boundaries = re.compile(r"([" + chars.DOTS_EXCEPT_APOSTROPHES + r"]+\s*)+")

    def __init__(self):
        super(FrMemorizingTokenizer, self).__init__()
        self.tokens = []
        self.char_registry = CharRegistry()
        self.normalizers: Tuple[ExcluderPrototype, ...] = (
            AujourdhuiExcluder(char_registry=self.char_registry),
            ApostropheExcluder(char_registry=self.char_registry),
            FrenchCliticsExcluder(char_registry=self.char_registry),
            CompoundAbbreviationsExcluder(abbrs=ABBREVIATIONS, ignore_case=False, char_registry=self.char_registry),
            ReferenceExcluder(char_registry=self.char_registry),
        )

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    def _real_sentence_tokenizer(self, string: str) -> List[str]:
        string = self.re_sentence_boundaries.sub(self._sentence_tokenizer_merge_matches, string)

        for excluder in self.normalizers:
            string = excluder.after_sentence_tokenizer(string)

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

        return self.re_remove_ending_apostrophe.sub("'", inp)\
            .replace("-t-", "-")  # Temp feature until retrain has been done
