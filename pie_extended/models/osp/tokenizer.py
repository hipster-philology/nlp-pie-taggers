import regex as re
from typing import List, Generator, Tuple

from pie_extended.models.fro.tokenizer import _Dots_except_apostrophe
from pie_extended.models.osp._params import ABBREVIATIONS
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.pipeline.tokenizers.utils.excluder import (
    ReferenceExcluder,
    ExcluderPrototype,
    RegexpExcluder,
    CompoundAbbreviationsExcluder,
    DEFAULT_CHAR_REGISTRY
)


class OspMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )

    def __init__(self):
        super(OspMemorizingTokenizer, self).__init__()
        self.tokens = []
        self.char_registry = DEFAULT_CHAR_REGISTRY
        self.normalizers: Tuple[ExcluderPrototype, ...] = (
            ReferenceExcluder(char_registry=self.char_registry),
            ReferenceExcluder(regex_string=r"(\[IGN:[^\]]+\])", char_registry=self.char_registry),
            RegexpExcluder(r"(\p{Greek}+)"),
            RegexpExcluder(r"(\p{No})"),
            CompoundAbbreviationsExcluder(abbrs=ABBREVIATIONS, ignore_case=False, char_registry=self.char_registry)
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

        >>> x = OspMemorizingTokenizer()
        >>> list(x.sentence_tokenizer("El rey don Alfonso fabló. Dixo Sr. Cid."))
        [['El', 'rey', 'don', 'Alfonso', 'fabló', '.'], ['Dixo', 'Sr.', 'Cid', '.']]

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

    def replacer(self, inp: str):
        return inp
