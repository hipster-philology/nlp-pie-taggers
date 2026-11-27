""" Disambiguation of lemmas with a lexicon built from an annotated corpus.

Some lemmas are numbered to tell homographs apart (`qui1`, `qui2`, `sum1`...). The number often follows from another
annotation: the part of speech. A lexicon says, for a lemma, which number goes with which category, and the model
does not need to learn it.

These classes were the library `autodisambiguator` (``autocat``) by the same author, now part of Pie Extended.
The lexicons themselves are built from a corpus with `pie_extended.pipeline.disambiguators.detector`
(or `pie-extended build-lexicons`).

Each class takes the annotations of a token as a dictionary (`{"lemma": "qui", "pos": "PROint"}`) and gives back what
has to be added to the lemma, or None.
"""
import abc
import json
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple

Default_lemma_key = "lemma"
Default_return_char = "?"
Default_join_string = "_"


class ProtoDisambiguator:
    """ Something that tells what to add to a lemma, given the annotations of the token """
    known_tokens: Set[str]

    @abc.abstractmethod
    def disambiguate(self, tasks: Dict[str, Any]) -> Optional[str]:
        """ What to add to the lemma of a token whose annotations are `tasks`, None if nothing """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_file(cls, filepath, lemma_key=Default_lemma_key, **kwargs):
        raise NotImplementedError

    def disambiguate_rows(self, rows: Iterable[Dict[str, Any]]) -> Iterator[str]:
        """ `disambiguate` for each token of a sentence (an empty string for no disambiguation) """
        for row in rows:
            yield self.disambiguate(row) or ""


def _load(filepath):
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


class NeedsDisambiguation(ProtoDisambiguator):
    """ Marks the lemmas that need a disambiguation, whatever it is

    >>> needs = NeedsDisambiguation(["qui", "sum"])
    >>> needs.disambiguate({"lemma": "qui"}), needs.disambiguate({"lemma": "amo"})
    ('?', None)
    """
    def __init__(self, categorizable: List[str], lemma_key: str = Default_lemma_key, return_char=Default_return_char):
        self.return_char = return_char
        self.categorizable = categorizable
        self.lemma_key = lemma_key
        self.known_tokens = set(categorizable)

    def disambiguate(self, tasks):
        lemma = tasks[self.lemma_key]
        if lemma in self.categorizable:
            return self.return_char

    @classmethod
    def from_file(cls, filepath, return_char=Default_return_char, lemma_key=Default_lemma_key):
        """ From a JSON file: a list of lemmas """
        return cls(return_char=return_char, categorizable=_load(filepath), lemma_key=lemma_key)


class CategoryAutodisambiguation(ProtoDisambiguator):
    """ Disambiguation that follows from another annotation (the part of speech, for example)

    >>> by_pos = CategoryAutodisambiguation("pos", {"qui": {"PROrel": "1", "PROint": "2"}})
    >>> by_pos.disambiguate({"lemma": "qui", "pos": "PROint"})
    '2'
    >>> by_pos.disambiguate({"lemma": "qui", "pos": "ADV"}) is None, by_pos.disambiguate({"lemma": "amo", "pos": "VER"})
    (True, None)
    """
    def __init__(
            self,
            category_key: str,
            categorizable: Dict[str, Dict[str, str]],
            lemma_key: str = Default_lemma_key,
    ):
        self.category_key = category_key
        self.lemma_key = lemma_key
        self.categorizable: Dict[str, Dict[str, str]] = categorizable
        self.known_tokens = set(self.categorizable.keys())

    def disambiguate(self, tasks) -> Optional[str]:
        lemma = tasks[self.lemma_key]
        if lemma in self.categorizable:
            cat = tasks.get(self.category_key, None)
            return self.categorizable[lemma].get(cat, None)

    @classmethod
    def from_file(cls, filepath, category_key=None, lemma_key=Default_lemma_key):
        """ From a JSON file: for each lemma, what to add for each category (`{"qui": {"PROint": "2"}}`) """
        if not category_key:
            raise AssertionError("A CategoryDisambiguator should have a `category_key` parameter at loading time")
        return cls(category_key=category_key, categorizable=_load(filepath), lemma_key=lemma_key)


class StraightAutodisambiguation(ProtoDisambiguator):
    """ Lemmas that have only one possible disambiguation

    >>> straight = StraightAutodisambiguation({"sum": "1"})
    >>> straight.disambiguate({"lemma": "sum"}), straight.disambiguate({"lemma": "qui"})
    ('1', None)
    """
    def __init__(
            self,
            categorizable: Dict[str, str] = None,
            lemma_key: str = Default_lemma_key
    ):
        self.lemma_key = lemma_key
        self.categorizable: Dict[str, str] = categorizable
        self.known_tokens = set(self.categorizable.keys())

    @classmethod
    def from_file(cls, filepath, lemma_key=Default_lemma_key, **kwargs):
        """ From a JSON file: for each lemma, what to add (`{"sum": "1"}`) """
        return cls(categorizable=_load(filepath), lemma_key=lemma_key)

    def disambiguate(self, tasks):
        lemma = tasks[self.lemma_key]
        return self.categorizable.get(lemma, None)


class GroupAutodisambiguation(ProtoDisambiguator):
    """ Tries several disambiguators in order: the first one that has an answer wins

    >>> straight = StraightAutodisambiguation({"sum": "1"})
    >>> by_pos = CategoryAutodisambiguation("pos", {"qui": {"PROint": "2"}})
    >>> group = GroupAutodisambiguation((straight, by_pos))
    >>> list(group.disambiguate_rows([
    ...     {"lemma": "sum", "pos": "VER"}, {"lemma": "qui", "pos": "PROint"}, {"lemma": "amo", "pos": "VER"}]))
    ['1', '2', '']
    """
    def __init__(self, categorizers: Tuple[ProtoDisambiguator, ...], lemma_key: str = Default_lemma_key):
        self.categorizers = categorizers
        self.lemma_key = lemma_key

        self.known_tokens = set()
        for cat in self.categorizers:
            self.known_tokens.update(cat.known_tokens)

    def disambiguate(self, tasks):
        lemma = tasks[self.lemma_key]
        if lemma in self.known_tokens:
            for categorizer in self.categorizers:
                val = categorizer.disambiguate(tasks)
                if val:
                    return val
