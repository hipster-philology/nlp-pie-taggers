from abc import ABC
import regex as re
from typing import Match, List, Optional

# Common values so that there is not (too much) collision
DOT = '語'
COLON = '桁'
BRACKET_L = '左'
BRACKET_R = '右'


class ExcluderPrototype(ABC):
    """Excluders should be used to remove dots and the likes from string before sentence tokenization.
    Data can be reintroduce later with their .denormalize() method"""
    def before_sentence_tokenizer(self, value: str) -> str:
        raise NotImplementedError

    def after_sentence_tokenizer(self, value: str) -> str:
        raise NotImplementedError

    @property
    def can_be_replaced(self) -> bool:
        return True

    @property
    def exclude_regexp(self) -> Optional[re.Regex]:
        return None


class ReferenceExcluder(ExcluderPrototype):
    """ Allows for exclusion of reference tokens such as [REF:1.b.Z] """

    def __init__(self,
                 dot: str = DOT,
                 colon: str = COLON,
                 bracket_l: str = BRACKET_L,
                 bracket_r: str = BRACKET_R
                 ):
        self.dot: str = dot
        self.colon: str = colon
        self.bracket_r: str = bracket_r
        self.bracket_l: str = bracket_l
        self.re: re.Regex = re.compile(r"(\[REF:[A-Za-z0-9\.]+\])")

    @property
    def can_be_replaced(self) -> bool:
        return False

    @property
    def exclude_regexp(self) -> Optional[re.Regex]:
        return self.re

    def _replace_in(self, match: Match) -> str:
        return " " + match.group()\
            .replace(".", self.dot)\
            .replace(":", self.colon)\
            .replace("[", self.bracket_l)\
            .replace("]", self.bracket_r)+ " "

    def before_sentence_tokenizer(self, value: str) -> str:
        """ Normalize a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = ReferenceExcluder()
        >>> excl.before_sentence_tokenizer("Choubidou [REF:1.a.Z] choubida [REF:1.b.Z]")
        'Choubidou 左REF桁1語a語Z右 choubida 左REF桁1語b語Z右'

        """
        return self.re.sub(self._replace_in, value)

    def after_sentence_tokenizer(self, value: str) -> str:
        """ Reset the state of a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = ReferenceExcluder()
        >>> excl.after_sentence_tokenizer('Choubidou 左REF桁1語a語Z右 choubida 左REF桁1語b語Z右')
        'Choubidou [REF:1.a.Z] choubida [REF:1.b.Z]'

        """
        return value\
            .replace(self.dot, ".")\
            .replace(self.colon, ":")\
            .replace(self.bracket_l, "[")\
            .replace(self.bracket_r, "]")

    def ignore(self, string: str) -> bool:
        return bool(self.re.match(string))


class AbbreviationsExcluder(ExcluderPrototype):
    def __init__(self, abbrs: List[str], dot: str = DOT, apply_replacements: bool = True):
        """

        :param: List of abbreviation (dot included), eg. ['cf.', 'p.']
        """
        self.dot = dot
        self.re = re.compile(
            r"("+r"|".join([abbr.replace(".", "") for abbr in abbrs])+r")(\.)"
        )
        self._apply_replacements = apply_replacements

    def _replace_in(self, match: Match) -> str:
        return match.group()\
            .replace(".", self.dot)

    @property
    def can_be_replaced(self) -> bool:
        return self._apply_replacements

    @property
    def exclude_regexp(self) -> Optional[re.Regex]:
        return self.re

    def before_sentence_tokenizer(self, value: str) -> str:
        """ Normalize a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = AbbreviationsExcluder(['cf.', 'p.'])
        >>> excl.before_sentence_tokenizer("cf. p. 45 et les. points.")
        'cf語 p語 45 et les. points.'

        """
        return self.re.sub(self._replace_in, value)

    def after_sentence_tokenizer(self, value: str) -> str:
        """ Reset the state of a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = AbbreviationsExcluder(['cf.', 'p.'])
        >>> excl.after_sentence_tokenizer('cf語 p語 45 et les. points.')
        'cf. p. 45 et les. points.'

        """
        return value.replace(
            self.dot, '.'
        )
