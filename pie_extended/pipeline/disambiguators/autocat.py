from autocat.autocat import ProtoDisambiguator, NeedsDisambiguation
from .proto import Disambiguator
from typing import Optional, Set


class Autocat(Disambiguator):
    def __init__(self, autocat_categorizer: ProtoDisambiguator, separator: str = "", **kwargs):
        self.autocat_categorizer: ProtoDisambiguator = autocat_categorizer
        self.lemma_key = autocat_categorizer.lemma_key
        self.separator = separator

    def __call__(self, sent, tasks):
        toks, sents_as_rows = zip(*[
            (token, dict(zip(tasks, tags)))
            for token, tags in sent
        ])

        out = [
        ]

        for (tok, tags, dis) in zip(toks, sents_as_rows, self.autocat_categorizer.disambiguate_rows(sents_as_rows)):
            if dis:
                tags[self.lemma_key] += dis
            out.append((tok, list(tags.values())))

        return out


class DisambiguationAsTask(ProtoDisambiguator):
    def __init__(self,
                 impossible_disambiguator: NeedsDisambiguation,
                 task_name: str = "Dis", separator: str = "",
                 undisambiguated_marker: str = "?",
                 lemma_key: str = "lemma", empty_value: str = "_"
                 ):
        self.task_name: str = task_name
        self.undisambiguated_marker: str = undisambiguated_marker
        self.separator: str = separator
        self.lemma_key: str = lemma_key
        self.empty_value: str = empty_value
        self.impossible_disambiguator: NeedsDisambiguation = impossible_disambiguator

    @property
    def known_tokens(self) -> Set[str]:
        return self.impossible_disambiguator.known_tokens

    def disambiguate(self, tasks) -> Optional[str]:
        disamb = self.impossible_disambiguator.disambiguate(tasks)
        if disamb and tasks[self.task_name] != self.undisambiguated_marker:
            disamb = tasks[self.task_name]
            if disamb == self.empty_value:
                return self.undisambiguated_marker
            return disamb
        else:
            return disamb

    @classmethod
    def from_file(cls, filepath, lemma_key="", **kwargs):
        return None
