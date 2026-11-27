import regex as re
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from typing import List, Generator, Tuple
import unicodedata
from pie_extended.pipeline.tokenizers.utils.excluder import (
    ReferenceExcluder,
    DEFAULT_CHAR_REGISTRY,
    ApostropheExcluder,
    chars
)

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"
_SpaceNormalizer = re.compile(r"(\s+)")
_APO = chars.APOSTROPHE

# Substitutions applied by `_real_word_tokenizer`, compiled once at import (order matters)
_I = re.IGNORECASE
_PRE_SUBS = [
    (re.compile(rf"((?:qu)|[dl])[{_APO}]"), r"\1' "),
    (re.compile(r'(\d)\s(\d)'), r'\1<PPLesp>\2'),
]
_WORD_SUBS = [
    (re.compile(r"(-[nz]-)(\P{L}*)", _I), r"\t\1\t\2"),  # pas d'espace
    (re.compile(r"(\P{L}|^)" + rf"([dlmnst][{_APO}])", _I), r"\1\t\2\t"),  # espace avant
    (re.compile(r"(\P{L}|^)(\p{L}*[qnv][us]" + rf"[{_APO}])", _I), r"\1\t\2\t"),  # espace avant
    (re.compile(r"(\P{L}|^)(\p{L}*" + rf"qu[{_APO}])", _I), r"\1\t\2\t"),  # espace avant  # TODO Duplicate of [qnv][us]' ?
    (re.compile(r"(\P{L}|^)(\p{L}*" + rf"ent[{_APO}])", _I), r"\1\t\2\t"),  # espace avant
    (re.compile(r"(\P{L}|^)(\p{L}*" + rf"[çcbzu][{_APO}])", _I), r"\1\t\2\t"),  # espace avant  # TODO Merge with [dlmnst] ?
    (re.compile(r"([\p{L}\d]+(\.[\p{L}\d]+)+)"), r"\t\1\t"),  # espace avant et après
    (re.compile(r"\.($|\P{L})"), r"\t.\1"),
    (re.compile(r"(\D|^),"), r"\1\t,\t"),
    (re.compile(r",($|\D)"), r"\t,\t\1"),
    (re.compile(rf"-(vos|ne|[st][eu]?[{_APO}]?|l[aoi{_APO}]s?|me|d[{_APO}]|en|[nv]os|u)" + r"($|\P{L})", _I), r"\t-\1\t\2"),  # espace après  # TODO Try to simplify ?
    (re.compile(rf"[{_APO}]" + r"([unv]\p{L}*)($|\P{L})", _I), r"\t'\1\t\2"),  # règle pour 'u 'us 'n 'v 'ns 'vs... # espace après
    (re.compile(rf"[{_APO}]" r"([dlmnsti])($|\P{L})", _I), r"\t'\1\t\2"),  # règle pour 'm 't 'i 's 'ac ... # espace après
    (re.compile(r"(\p{P})(\p{P})"), r"\t\1\t\2\t"),
    (re.compile(r"<PPLesp>"), ' '),
    (re.compile(r"([<>])"), r"\t\1\t"),
]


class OccMemorizingTokenizer(MemorizingTokenizer):
    """ Occitan Tokenizer with memorizing capacities (for normalization steps)

    This tokenizer is based on a Perl script published by Marianne Verges-Couret in 2019
    (https://zenodo.org/records/2533873), as well as the description for the Python tokenizer described in
    (Miletić, 2023) that was also derived from the work in project RESTAURE.
    It was adapted by Oriane Nedey in python and then adapted to Pie-Extended
    """
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")

    # Define a pattern that matches any punctuation or symbol, with exceptions
    re_in_non_amb = re.compile(rf"(?![{_APO}\-,.<>])"+r"[\p{P}\p{S}]")

    # Define a pattern that matches (XML/HTML...) tags  # ToDO check that this change is ok
    re_tags = re.compile(r'(<\\?[^\d\s].*>)')

    re_split_match = re.compile(rf"(\.{2,})|({re_in_non_amb.pattern})|{re_tags.pattern}")

    def __init__(self):
        super(OccMemorizingTokenizer, self).__init__()
        self.tokens = []
        self.char_registry = DEFAULT_CHAR_REGISTRY
        self.normalizers: Tuple[ReferenceExcluder] = (
            ReferenceExcluder(char_registry=self.char_registry),
        )
        self.re_split_step_one = re.compile(
            rf"(?:{self.normalizers[0].re.pattern})|({self.re_in_non_amb.pattern}|\s|\.{2,}|{self.re_tags.pattern})"
        )

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    def _real_sentence_tokenizer(self, string: str) -> List[str]:
        string = _SpaceNormalizer.sub(" ", string.strip())
        string = self._sentence_boundaries.sub(self._sentence_tokenizer_merge_matches, string)

        for normalizer in self.normalizers:
            string = normalizer.after_sentence_tokenizer(string)

        return string.split("<SPLIT>")

    def _real_word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        """
        Segments a string into a list of tokens by applying Occitan-specific regular expressions.

        :param text: string, ideally one single segment.
        :returns: list of segmented tokens
        """
        res = []
        # Normalize apostrophe of qu' d' l'
        # ToDo: Unclear if we should not simply use the regulizer for apostrophes...
        # ToDo: Unclear if it is not already taken care of by the rest of the regexp
        text = _PRE_SUBS[0][0].sub(_PRE_SUBS[0][1], text)
        text = _PRE_SUBS[1][0].sub(_PRE_SUBS[1][1], text)
        for m in self.re_split_step_one.split(text):
            if not m or not m.strip():
                continue
            elif self.normalizers[0].re.match(m):
                res.append(m)
            elif self.re_split_match.match(m):
                res.append(m)
            else:
                for pattern, replacement in _WORD_SUBS:
                    m = pattern.sub(replacement, m)
                res.extend(m.split('\t'))

        # Remove empty tokens
        res = [item for item in res if item.strip()]
        return res

    def normalizer(self, data: str) -> str:
        for excluder in self.normalizers:
            data = excluder.before_sentence_tokenizer(data)
        return data

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        sentences = list()
        data = self.normalizer(text)
        for sent in self._real_sentence_tokenizer(data):
            sent = sent.strip()
            if sent:
                sentences.append(self.word_tokenizer(sent))
        yield from sentences

    def replacer(self, inp: str):
        for excluder in self.normalizers:
            if excluder.exclude_regexp.match(inp):
                if excluder.can_be_replaced:
                    return inp

        return unicodedata.normalize("NFKC", inp)
