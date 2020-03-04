import regex as re
from typing import Dict, Pattern

from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor
from pie_extended.pipeline.postprocessor.proto import RenamedTaskProcessor


class FrRulesProcessor(RuleBasedProcessor):

    def __init__(self, *args, **kwargs):
        super(FrRulesProcessor, self).__init__(*args, **kwargs)


class FrGlueProcessor(GlueProcessor):
    """ We glue morphological features into one column

    """
    OUTPUT_KEYS = ["form", "lemma", "POS", "morph"]
    GLUE = {"morph": ["MODE", "TEMPS", "PERS.", "NOMB.", "GENRE", "CAS"]} #, "DEGRE"]}
    EMPTY_TAG: Dict[str, str] = {"CAS": "x", "NOMB.": "x", "DEGRE": "x", "MODE": "x", "TEMPS": "x", "GENRE": "x",
                                 "PERS.": "x"}

    def __init__(self, *args, **kwargs):
        super(FrGlueProcessor, self).__init__(*args, **kwargs)