import regex as re
from typing import Dict

from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype

_PUNCT = re.compile(r"^[\W_]+$")


class OspPunctProcessor(ProcessorPrototype):
    """ Reinserted punctuation gets the model's PUNCT tag and is its own lemma

    >>> x = OspPunctProcessor()
    >>> x.set_tasks(["lemma", "POS"])
    ['lemma', 'POS']
    >>> x.reinsert("¶") == {"form": "¶", "lemma": "¶", "POS": "PUNCT"}
    True
    >>> x.reinsert("[REF:1]") == {"form": "[REF:1]", "lemma": "_", "POS": "_"}
    True
    """

    def reinsert(self, form: str) -> Dict[str, str]:
        annotations = super(OspPunctProcessor, self).reinsert(form)
        if _PUNCT.match(form):
            if "lemma" in annotations:
                annotations["lemma"] = form
            if "POS" in annotations:
                annotations["POS"] = "PUNCT"
        return annotations
