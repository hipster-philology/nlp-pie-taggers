import regex as re
from typing import Dict, Pattern

from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor
from pie_extended.pipeline.postprocessor.proto import RenamedTaskProcessor


class FroRulesProcessor(RuleBasedProcessor):
    """ Fro Dataset has not all punctuation signs in it, we remove it and posttag it automatically

    """
    PONCTU: Pattern = re.compile(r"^\W+$")
    NUMBER: Pattern = re.compile(r"\d+")
    PONFORT = [".", "...", "!", "?"]

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        token = annotation["form"]
        if self.PONCTU.match(token):
            if token in self.PONFORT:
                pos = "PONfrt"
            else:
                pos = "PONfbl"
            return {"form": token, "lemma": token, "POS": pos, "morph": "MORPH=empty", "treated": token}
        elif self.NUMBER.match(token):
            annotation["pos"] = "ADJcar"
        return annotation

    def __init__(self, *args, **kwargs):
        super(FroRulesProcessor, self).__init__(*args, **kwargs)


class FroGlueProcessor(GlueProcessor):
    """ We glue morphological features into one column

    """
    OUTPUT_KEYS = ["form", "lemma", "POS", "morph"]
    GLUE = {"morph": ["MODE", "TEMPS", "PERS.", "NOMB.", "GENRE", "CAS", "DEGRE"]}
    EMPTY_TAG: Dict[str, str] = {"CAS": "_", "NOMB.": "_", "DEGRE": "_", "MODE": "_", "TEMPS": "_", "GENRE": "_",
                                 "PERS.": "_"}

    def __init__(self, *args, **kwargs):
        super(FroGlueProcessor, self).__init__(*args, **kwargs)