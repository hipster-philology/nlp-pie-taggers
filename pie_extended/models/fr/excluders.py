from typing import Tuple, Match
import regex as re

from pie_extended.pipeline.tokenizers.utils.excluder import ExcluderPrototype, DASH, APOSTROPHE
from pie_extended.pipeline.tokenizers.utils import chars


AUJOURDHUI_MASK = "字"
CLITICS = tuple(sorted([
    '-ce', '-ci', '-elle', '-elles', '-en', '-eux', '-il', '-ils', '-je', '-la', '-le',
    '-les', '-leur', '-leurs',
    '-lui', '-là', '-m', '-me', '-moi', '-même', '-mêmes', '-nous', '-on', '-t',
    '-te', '-toi', '-tu', '-un',
    '-une', '-unes', '-uns', '-vous', '-y',
    # No idea what was the goal of the following line...
    # r'-m字\d', r'-t字\d'  # 字 replaces all kinds of apostrophe
], key=len, reverse=True))

# Abbreviations separated by `; ` (SEMICOLON+SPACE)
# You can use regexp inside this list, such as [Cc]f. but I would rather recommend to add both `cf.; Cf;`
#   for readability.
ABBREVIATIONS = sorted(list(set(
    "Acad.; Adj.; Agricol.; Agricul.; Apocal.; anc.; Bot.; Botan.; Botaniq.; ca.; cap.; capi.; cf.; Cf.; " 
    "Cha.; Chap.; Col.; Dic.; Diction.; Dictionn.; Eccl.; Écon.; Élem.; Fig.; Fr.; Geog.; Gram.; " 
    "Gramm.; Hist.; Ibid.; Ibid.; Inst.; Jard.; Jurisprud.; Latit.; Li.; Lib.; Libr.; Lig.; Lit.; " 
    "Littérat.; Liv.; Long.; Mar.; Mat.; Mathém.; Mech.; Med.; Med.; Mem.; Menuis.; Milit.; Mod.; " 
    "Mor.; Mr.; Monsr.; nat.; natur.; N.b.; Orat.; Ornith.; Ornythol.; Ornitholog.; Part.; Pag.; " 
    "Pharm.; Phil.; Philos.; Pl.; Pl.; Politiq.; P.S.; Phys.; Physiq.; Sr.; St.; Subst.; s.f.; " 
    "S.M.; s.m.; Tab.; Théât.; Trév.; Tom.; Vol.; V. n.; V. a.; V. act.; Zoo.; " 
    "Zoolog.".split("; ")
)), key=len, reverse=True)


class AujourdhuiExcluder(ExcluderPrototype):
    """ Normalizes Aujourd'hui before it goes into splitting sentences

    >>> excl = AujourdhuiExcluder()
    >>> excl.before_sentence_tokenizer("Aujourd'hui j'ai poney")
    "Aujourd字0hui j'ai poney"
    >>> excl.after_sentence_tokenizer("Aujourd字0hui j'ai poney")
    "Aujourd'hui j'ai poney"
    """
    def __init__(self, apostrophe: str = chars.APOSTROPHE, apostrophe_mask: str = AUJOURDHUI_MASK):
        self.apostrophes = apostrophe
        self.mask = apostrophe_mask
        self.re = re.compile("(aujourd)(["+self.apostrophes+"])(hui)", flags=re.IGNORECASE)

    def _replace(self, regex_match: Match) -> str:
        return regex_match.group(1) + self.mask + str(self.apostrophes.index(regex_match.group(2))) + regex_match.group(3)

    def before_sentence_tokenizer(self, value: str) -> str:
        return self.re.sub(self._replace, value)

    def after_sentence_tokenizer(self, value: str) -> str:

        for index_apo, apostrophe in enumerate(self.apostrophes):
            value = value.replace(self.mask+str(index_apo), apostrophe)
        return value


class FrenchCliticsExcluder(ExcluderPrototype):
    def __init__(self, clitics: Tuple[str, ...] = CLITICS, dash: str = DASH,
                 add_space_before: bool = True, add_space_after: bool = True,
                 apostrophes: str = chars.APOSTROPHE, apostrophes_mask: str = APOSTROPHE):
        self.clitics = clitics
        self.dash = dash
        self.apostrophes = apostrophes
        self.apostrophes_mask = apostrophes_mask
        self.re = re.compile(
            r"((-)(t))?(-)(" +
            r"|".join([tok.replace("-", "") for tok in self.clitics]) +
            # We use apostrophe_mask and the \d because a mask could have already been applied
            r")([" + self.apostrophes + r"]|" + self.apostrophes_mask + r"\d|\b|$)",
            flags=re.IGNORECASE
        )

        # Space handling
        self.space_before: str = ""
        if add_space_before:
            self.space_before = " "

        self.space_after: str = ""
        if add_space_after:
            self.space_after = " "

    def _replace_clitic(self, match: Match) -> str:
        # Group 1: - (of -t)
        # Group 2: t (of -t)
        # Group 3: - (of clitic)
        # Group 4: t (the clitic)
        # Group 5: apostrophe or word boundary
        g0, g1, g2, g3, g4, g5 = match.groups()
        before = ""
        if g0:
            before = self.dash+"t"

        return self.space_before + before + self.dash + g4 + g5 + self.space_after

    def before_sentence_tokenizer(self, value: str) -> str:
        """ Normalize before sentence is tokenized

        >>> excl = FrenchCliticsExcluder()
        >>> excl.before_sentence_tokenizer("A-t-il mangé le peut-être que moi-même je connais ?")
        'A 精t精il  mangé le peut-être que moi 精même  je connais ?'

        Note that it introduces a secondary space.

        >>> excl.before_sentence_tokenizer("Va-t'en va-nu-pieds !")
        "Va 精t' en va-nu-pieds !"

        """
        return self.re.sub(
            self._replace_clitic,
            value
        )

    def after_sentence_tokenizer(self, value: str) -> str:
        return value.replace(self.dash, "-")
