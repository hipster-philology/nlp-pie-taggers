import regex as re
from typing import List, Generator

from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"
_Dots_collections = r"[" + _Dots_except_apostrophe + "‘’]"
_RomanNumber = r"(?:M{1,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|C?D|D?C{1,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|M{0,4}" \
               r"(?:CM|CD|D?C{0,3})(?:XC|X?L|L?X{1,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|CD|D?C{0,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|I?V|V?I{1,3}))"


class FroMemorizingTokenizer(MemorizingTokenizer):
    APOSTROPHES = "'’ʼ"
    re_elision_apostrophe = re.compile(r"(\w+)([" + APOSTROPHES + r"])(\w+)")
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    re_add_space_around_apostrophe_that_are_quotes = re.compile(
        r"("
        r"(((?<=[\W])[\'’ʼ]+(?=[\W]))|"
        r"((?<=[\w])[\'’ʼ]+(?=[\W]))|"
        r"((?<=[\W])[\'’ʼ]+(?=[\w])))|"
        r"(^[\'’ʼ]+)|"
        r"([\'’ʼ]+$))"
        # NotLetter+Apo+NotLetter or Letter+Apo+NotLetter or NotLetter+Apo+Letter + Starting or ending apostrophe
        # ?'. or manger'_ or _'Bonjour
    )
    re_add_space_after_apostrophe = re.compile(r"(\s*)([\'’ʼ])(\s*)")
    re_remove_ending_apostrophe = re.compile(r"(?<=\w)([\'’ʼ])")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    roman_number_dot = re.compile(r"\.(" + _RomanNumber + r")\.")

    def __init__(self):
        super(FroMemorizingTokenizer, self).__init__()
        self.tokens = []

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    def _real_sentence_tokenizer(self, string: str) -> List[str]:
        string = self._sentence_boundaries.sub(self._sentence_tokenizer_merge_matches, string)
        string = string.replace("_DOT_", ".")
        for index_apo, apo in enumerate(self.APOSTROPHES):
            string = string.replace("ApOsTrOpHe"+str(index_apo), apo+" ")
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

    def apostrophe_replace(self, regex_match) -> str:
        return regex_match.group(1) + "ApOsTrOpHe"+ str(self.APOSTROPHES.index(regex_match.group(2))) + regex_match.group(3)

    def normalizer(self, data: str) -> str:
        data = self.re_add_space_around_punct.sub(
                    r" \g<2> ",
                    self.re_elision_apostrophe.sub(
                        self.apostrophe_replace,
                        self.roman_number_dot.sub(
                            r"_DOT_\g<1>_DOT_",
                            data
                        )
                    )
        )
        return data

    def replacer(self, inp: str):
        return self.re_remove_ending_apostrophe.sub("", inp)
