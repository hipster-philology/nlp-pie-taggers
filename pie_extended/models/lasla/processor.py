import regex as re
from typing import Dict

from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor


class LatinRulesProcessor(RuleBasedProcessor):
    """ Lasla data has no punctuation, we tag it automatically.

    "ne" token can be two different lemma, but I don't remember why I wrote this part. (ne/nec ?)

    """
    PONCTU = re.compile(r"^\W+$")

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        # If Else condition
        token = annotation["form"]

        if self.PONCTU.match(token):
            return {"form": token, "lemma": token, "pos": "PUNC", "morph": "MORPH=empty",
                    "treated": annotation['treated']}
        elif token.startswith("-"):
            if token == "-ne":
                annotation["lemma"] = "ne2"
            else:
                annotation["lemma"] = "ne"
        return annotation

    def __init__(self, *args, **kwargs):
        super(LatinRulesProcessor, self).__init__(*args, **kwargs)


class LatinGlueProcessor(GlueProcessor):
    OUTPUT_KEYS = ["form", "lemma", "pos", "morph"]
    GLUE = {"morph": ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]}
    WHEN_EMPTY = {"morph": "MORPH=empty"}

    def __init__(self, *args, **kwargs):
        super(LatinGlueProcessor, self).__init__(*args, **kwargs)
