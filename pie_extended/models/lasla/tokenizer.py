import regex as re
import click
import sys
from typing import List, Generator

from pie_extended.models.fro.tokenizer import _Dots_except_apostrophe, _RomanNumber
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.models.lasla._params import ne_and_n, latin_replacements, ve

try:
    import cltk
    from cltk.tokenize.latin.word import WordTokenizer
except ImportError as E:
    click.echo(click.style("You need to install cltk and its Latin Data to runs this package", fg="red"))
    click.echo("pip install https://github.com/PonteIneptique/cltk/archive/latin_clitics_exceptions.zip")
    click.echo("pie-extended install-addons lasla")
    sys.exit(0)


ENCLITICS = ['que', 'n', 'ne', 'ue', 've', 'st']
BASE_ENCLITICS_EXCEPTIONS = set(ENCLITICS + cltk.tokenize.latin.params.latin_exceptions + ne_and_n + ve)
ENCLITIC_EXCEPTIONS = list([
    token
    for token in BASE_ENCLITICS_EXCEPTIONS
])
ENCLITIC_EXCEPTIONS += [
    token.lower().replace("v", "u").replace("j", "i")
    for token in BASE_ENCLITICS_EXCEPTIONS
]
ENCLITIC_EXCEPTIONS += [
    token.lower().replace("v", "u")
    for token in BASE_ENCLITICS_EXCEPTIONS
]
ENCLITIC_EXCEPTIONS += [
    token.lower().replace("j", "i")
    for token in BASE_ENCLITICS_EXCEPTIONS
]
ENCLITIC_EXCEPTIONS = set(ENCLITIC_EXCEPTIONS)


class LatMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    roman_number_dot = re.compile(r"\.(" + _RomanNumber + r")\.")

    def __init__(self):
        super(LatMemorizingTokenizer, self).__init__()
        self.tokens = []
        self._word_tokenizer = WordTokenizer()

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    @classmethod
    def _real_sentence_tokenizer(cls, string: str) -> List[str]:
        string = cls._sentence_boundaries.sub(cls._sentence_tokenizer_merge_matches, string)
        string = string.replace("_DOT_", ".")
        return string.split("<SPLIT>")

    def _real_word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        tokenized = [tok for tok in self._word_tokenizer.tokenize(
            text,
            replacements=latin_replacements,
            enclitics_exceptions=ENCLITIC_EXCEPTIONS
        ) if tok]
        if tokenized:
            tokenized = [tok.lower() for tok in tokenized]
        return tokenized

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

    def normalizer(self, data: str) -> str:
        data = self.re_add_space_around_punct.sub(
                    r" \g<2> ",
                    self.roman_number_dot.sub(
                        r"_DOT_\g<1>_DOT_",
                        data
                    )
                )
        return data

    def replacer(self, inp: str):
        inp = inp.replace("V", "U").replace("v", "u").replace("J", "I").replace("j", "i")
        return inp
