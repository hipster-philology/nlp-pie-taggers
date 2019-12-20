from autocat.autocat import ProtoDisambiguator
from .proto import Disambiguator


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

