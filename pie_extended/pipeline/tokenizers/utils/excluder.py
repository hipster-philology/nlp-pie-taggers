from abc import ABC
import regex as re
from typing import Match, List, Optional, Dict

import pie_extended.pipeline.tokenizers.utils.chars as chars
import pie_extended.pipeline.tokenizers.utils.regexps as regexps
import copy

# Common values so that there is not (too much) collision
DOT = '語'
COLON = '桁'
BRACKET_L = '左'
BRACKET_R = '右'
APOSTROPHE = '風'
DASH = "精"


_DEFAULT_CHAR_REGISTRY = {
    ".": '語',
    ":": '桁',
    '[': '左',
    ']': '右',
    "'": '風',
    "-": "精"
}


class CharRegistry:
    def __init__(self, use_default=True, unicode_start_range=0x8d00):
        self._char_to_code = {}
        if use_default:
            self._char_to_code.update(_DEFAULT_CHAR_REGISTRY)
        self._start_range = unicode_start_range

    def __getitem__(self, item):
        if item in self._char_to_code:
            return self._char_to_code[item]
        else:
            self._char_to_code[item] = chr(self._start_range + len(self._char_to_code))
            return self._char_to_code[item]

    def __setitem__(self, key, value):
        self._char_to_code[key] = value

    def items(self):
        return self._char_to_code.items()

    def __len__(self):
        return len(self._char_to_code)


DEFAULT_CHAR_REGISTRY = CharRegistry()


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
    """ Allows for exclusion of reference tokens such as [REF:1.b.Z]

    >>> ref = ReferenceExcluder()
    >>> ref.before_sentence_tokenizer("ici [REF:###abc??<>] Paris")
    'ici  左REF桁贆贆贆abc贉贉贇贈右  Paris'
    >>> ref.after_sentence_tokenizer('ici  左REF桁贆贆贆abc贉贉贇贈右  Paris')
    'ici  [REF:###abc??<>]  Paris'
     """

    def __init__(self,
                 regex_string: str = r"(\[REF:[^\]]+\])",
                 regex_needs_replacement: str = r"[^\w\s]",
                 char_registry: Optional[CharRegistry] = None
                 ):
        self.re: re.Regex = re.compile(regex_string)
        self.char_registry: CharRegistry = char_registry or CharRegistry()
        # Character that needs to be escaped.
        self.needs_replacement: re.Regex = re.compile(regex_needs_replacement)

    @property
    def can_be_replaced(self) -> bool:
        return False

    @property
    def exclude_regexp(self) -> Optional[re.Regex]:
        return self.re

    def _replace_in(self, match: Match) -> str:
        data = match.group()
        for char, repl in self.char_registry.items():
            data = data.replace(char, repl)

        for char in sorted(list(set(self.needs_replacement.findall(data)))):
            data = data.replace(char, self.char_registry[char])

        return f" {data} "

    def before_sentence_tokenizer(self, value: str) -> str:
        """ Normalize a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = ReferenceExcluder()
        >>> excl.before_sentence_tokenizer("Choubidou [REF:1.a.Z] choubida [REF:1.b.Z]")
        'Choubidou  左REF桁1語a語Z右  choubida  左REF桁1語b語Z右 '

        """
        return self.re.sub(self._replace_in, value)

    def after_sentence_tokenizer(self, value: str) -> str:
        """ Reset the state of a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = ReferenceExcluder()
        >>> excl.after_sentence_tokenizer('Choubidou 左REF桁1語a語Z右 choubida 左REF桁1語b語Z右')
        'Choubidou [REF:1.a.Z] choubida [REF:1.b.Z]'

        """
        for char, repl in self.char_registry.items():
            value = value.replace(repl, char)
        return value

    def ignore(self, string: str) -> bool:
        return bool(self.re.match(string))


class RegexpExcluder(ExcluderPrototype):
    def __init__(self, regex: str):
        """

        :param regex: Regular expression to exclude from tokenization

        Exclude data from tokenization

        >>> r = RegexpExcluder(r"(\p{No})")
        >>> r.can_be_replaced
        False
        >>> r.exclude_regexp.match("¹") is None
        False
        >>> r.exclude_regexp.match("2") is None
        True
        """
        self.re = re.compile(regex)

    @property
    def can_be_replaced(self) -> bool:
        return False

    @property
    def exclude_regexp(self) -> Optional[re.Regex]:
        return self.re

    def before_sentence_tokenizer(self, value: str) -> str:
        return value

    def after_sentence_tokenizer(self, value: str) -> str:
        return value


class AbbreviationsExcluder(ExcluderPrototype):
    def __init__(self, abbrs: List[str], apply_replacements: bool = True,
                 char_registry: Optional[CharRegistry] = None):
        """

        :param: List of abbreviation (dot included), eg. ['cf.', 'p.']
        """
        self.char_registry: CharRegistry = char_registry or CharRegistry()
        self.re = re.compile(
            r"("+r"|".join([abbr.replace(".", "") for abbr in abbrs])+r")(\.)"
        )
        self._apply_replacements = apply_replacements

    def _replace_in(self, match: Match) -> str:
        return match.group()\
            .replace(".", self.char_registry["."])

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
            self.char_registry["."], '.'
        )


class AbbreviationsRemoverExcluder(AbbreviationsExcluder):
    def after_sentence_tokenizer(self, value: str) -> str:
        """ Reset the state of a string before it goes into sentence tokenizing

        :param value: String to clean

        >>> excl = AbbreviationsRemoverExcluder(['cf.', 'p.'])
        >>> excl.after_sentence_tokenizer('cf語 p語 45 et les. points.')
        'cf p 45 et les. points.'

        """
        return value.replace(self.char_registry["."], '')


class CompoundAbbreviationsExcluder(AbbreviationsExcluder):
    def __init__(self, abbrs: List[str], apply_replacements: bool = True,
                 ignore_case: bool = True, char_registry: Optional[CharRegistry] = None):
        """

        >>> excl = CompoundAbbreviationsExcluder(["cf.", "V. act."])
        >>> excl.before_sentence_tokenizer("Cf. article 5, V. act. 9.")
        'Cf語 article 5, V語 act語 9.'
        >>> excl.after_sentence_tokenizer('Cf語 article 5, V語 act語 9.')
        'Cf. article 5, V. act. 9.'
        """
        super(CompoundAbbreviationsExcluder, self).__init__(abbrs, apply_replacements, char_registry=char_registry)
        re_kwargs = {}
        if ignore_case:
            re_kwargs["flags"] = re.IGNORECASE
        self.re = re.compile(
            r"\b("+"|".join([
                token.replace(" ", r"\s+").replace(".", r"\.")
                for token in abbrs
                if token  # Small check.
            ])+r")",
            **re_kwargs
        )


class DottedNumberExcluder(ExcluderPrototype):
    def __init__(self, number_regex: str = regexps.RomanNumbers,
                 char_registry: Optional[CharRegistry] = None):
        self.re = re.compile(r"\.(" + number_regex + r")\.")
        self.char_registry: CharRegistry = char_registry or CharRegistry()

    def before_sentence_tokenizer(self, value: str) -> str:
        return self.re.sub(
            r"{0}\g<1>{0}".format(self.char_registry["."]),
            value,
        )

    def after_sentence_tokenizer(self, value: str) -> str:
        return value.replace(
            self.char_registry["."], '.'
        )


class ApostropheExcluder(ExcluderPrototype):
    """Allows for keeping apostrophes that are the mark of an elision, mostly in French such as
    "l'abbé"
    """
    def __init__(self,
                 match_apostrophes=chars.APOSTROPHE,
                 apostrophe_mask=APOSTROPHE,
                 add_space_after: bool = True,
                 add_space_before: bool = False):
        self.apostrophes = match_apostrophes
        self.re: re.Regex = re.compile(r"(\w+)([" + self.apostrophes + r"])(\w+)")
        self.apostrophe_mask: str = apostrophe_mask

        # Space handling
        self.space_before: str = ""
        if add_space_before:
            self.space_before = " "

        self.space_after: str = ""
        if add_space_after:
            self.space_after = " "

    def _before_sentence_tokenizer(self, regex_match: Match) -> str:
        """ Given a match on `l'abbé` returns `l風0abbé` where
            風 is the character mask and 0 the index of the apostroph in the match_apostrophes value
        """
        return regex_match.group(1) + \
            self.apostrophe_mask + \
            str(self.apostrophes.index(regex_match.group(2))) + \
            regex_match.group(3)

    def before_sentence_tokenizer(self, value: str) -> str:
        """ Normalization run before sentence tokenization

        :param value: String to normalize before sentence is toknized

        >>> excl = ApostropheExcluder(add_space_after=True)
        >>> excl.before_sentence_tokenizer("l'abbé lorsqu’il")
        'l風0abbé lorsqu風1il'

        """
        return self.re.sub(
            self._before_sentence_tokenizer,
            value
        )

    def after_sentence_tokenizer(self, value: str) -> str:
        """ Normalization run after sentence tokenization

        :param value: String to normalize before sentence is toknized

        >>> excl = ApostropheExcluder(add_space_after=True)
        >>> excl.after_sentence_tokenizer('l風0abbé lorsqu風1il')
        "l' abbé lorsqu’ il"

        """
        for index_apo, apostrophe in enumerate(self.apostrophes):
            value = value.replace(
                self.apostrophe_mask+str(index_apo),
                self.space_before + apostrophe + self.space_after)
        return value
