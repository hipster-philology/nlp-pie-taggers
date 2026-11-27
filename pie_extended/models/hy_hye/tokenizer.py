import regex as re
from typing import Generator, List, Tuple

from pie_extended.pipeline.tokenizers.simple_tokenizer import SimpleTokenizer

# Armenian marks written on a vowel *inside* the word they belong to: emphasis (՛), exclamation (՜), question (՞).
# The Universal Dependencies treebanks the models are trained on make them a token of their own, placed after the
# word (multiword token `Մի՞թե` -> words `Միթե`, `՞`): the tokenizer does the same.
MARKS = "՛՜՞"
# Armenian letters (not `\p{Armenian}`: this script also contains the Armenian punctuation: ։ ՝ ֊ ...)
LETTERS = "\u0531-\u0556\u0560-\u0588"
# Apostrophe of the Western Armenian clitics (կ՚ուզեմ -> `կ՚`, `ուզեմ`): it stays on the clitic.
APOSTROPHE = "՚"

_MARKS = re.compile("[{}]".format(MARKS))
_TOKEN = re.compile(
    r"(?P<number>\d+(?:[.,]\d+)*)"                     # 1.000 2.37,8 (the UD treebanks keep them in one piece)
    r"|(?P<ellipsis>\.{2,}|…)"
    r"|(?P<word>[" + LETTERS + r"\p{M}\d_" + MARKS + r"]+" + APOSTROPHE + r"?)"
    r"|(?P<foreign>[^\W" + LETTERS + r"]+)"             # Latin... words: they never mix with Armenian letters
    r"|(?P<other>\S)"                                  # any other punctuation: one token each (hyphens too)
)
# End of a sentence (։ : ! ? …), possibly followed by closing quotes or brackets. The dot is *not* one: in these texts
# it is mostly an abbreviation, an initial or a number (Խ. Աբովյան, 2020թ.): on the dev sets of the three treebanks,
# counting it lowers the precision of the sentence boundaries from 85/90/53% to 99/98/94% (Eastern/Western/Classical).
_SENTENCE_END = re.compile(r"[։:!?…]+[»)\]”\"']*\s+")


class ArmenianTokenizer(SimpleTokenizer):
    """ Tokenizer for Eastern, Western and Classical Armenian, following the tokenization of their UD treebanks.

    Punctuation is made of tokens of their own, hyphens split words, numbers and ellipsis stay in one piece, and
    words do not mix scripts (`pensionnaireները` -> `pensionnaire`, `ները`).

    >>> tokenizer = ArmenianTokenizer()
    >>> list(tokenizer.sentence_tokenizer("Բարև աշխարհ։ Ինչպե՞ս ես՝ լավ, 1.000 դրամ..."))
    [['Բարև', 'աշխարհ', '։'], ['Ինչպես', '՞', 'ես', '՝', 'լավ', ',', '1.000', 'դրամ', '...']]

    The mark leaves its word: the word is written as it is in the text (`Ինչպե՞ս`) while the mark is not written
    anywhere (empty string), which `surface_tokens` tells for the computation of spaces between tokens:

    >>> tokenizer.surface_tokens()[3:6]
    ['Ինչպե՞ս', '', 'ես']
    """
    def __init__(self, segmenter=None):
        """
        :param segmenter: Object with a `cuts(word) -> List[int]` method that gives where a word is cut in several
            words (Classical Armenian clitics, see `pie_extended.models.hy_xcl.segmenter`). None: words are not cut.
        """
        super(ArmenianTokenizer, self).__init__()
        self.segmenter = segmenter
        self._surfaces: List[str] = []

    def reset(self):
        self._surfaces = []

    def surface_tokens(self) -> List[str]:
        return self._surfaces

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        self._surfaces = []
        start = 0
        for match in _SENTENCE_END.finditer(text):
            sentence = self.word_tokenizer(text[start:match.end()], lower=lower)
            if sentence:
                yield sentence
            start = match.end()
        sentence = self.word_tokenizer(text[start:], lower=lower)
        if sentence:
            yield sentence

    def _pieces(self, word: str, written: str) -> Tuple[List[str], List[str]]:
        """ The words a written word is made of, and how each of them is written

        >>> class AfterFirstLetter:
        ...     cuts = lambda self, word: [1]
        >>> ArmenianTokenizer(AfterFirstLetter())._pieces("զմեղս", "զմեղս")
        (['զ', 'մեղս'], ['զ', 'մեղս'])

        The marks stay with the piece they follow, whatever the place of the cut:

        >>> ArmenianTokenizer(AfterFirstLetter())._pieces("զինչ", "զի՞նչ")
        (['զ', 'ինչ'], ['զ', 'ի՞նչ'])
        """
        cuts = self.segmenter.cuts(word) if self.segmenter else []
        if not cuts:
            return [word], [written]
        bounds = [0] + list(cuts) + [len(word)]
        pieces = [word[start:end] for start, end in zip(bounds, bounds[1:])]
        # Place of each letter of the word in the written word (marks are not letters of the word)
        place = [index for index, character in enumerate(written) if character not in MARKS]
        starts = [0] + [place[cut] for cut in cuts]
        surfaces = [written[start:end] for start, end in zip(starts, starts[1:] + [len(written)])]
        return pieces, surfaces

    def word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        tokens: List[str] = []
        for match in _TOKEN.finditer(text):
            written = match.group()
            if match.lastgroup != "word":
                tokens.append(written)
                self._surfaces.append(written)
                continue

            word = _MARKS.sub("", written)
            marks = _MARKS.findall(written)
            if word:
                pieces, surfaces = self._pieces(word, written)
                tokens.extend(pieces)
                self._surfaces.extend(surfaces)
                for mark in marks:  # Not written anywhere: it comes from the word
                    tokens.append(mark)
                    self._surfaces.append("")
            else:  # Only marks: they were alone in the text
                for mark in marks:
                    tokens.append(mark)
                    self._surfaces.append(mark)

        if lower:
            tokens = [token.lower() for token in tokens]
        return tokens
