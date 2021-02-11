from typing import Dict, List


from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype


class GreekMorphProcessor(GlueProcessor):
    """

    >>> m = GreekMorphProcessor(head_processor=ProcessorPrototype())
    >>> m.set_tasks(["case", "degree", "gend", "lemma", "mood", "num", "pers", "pos", "tense", "voice"])
    ['lemma', 'pos', 'morph']
    >>> m.get_dict("Θύρσις", ["n", "-", "f", "θύρσις", "-", "s", "-", "n", "-", "-"])
    [{'form': 'Θύρσις', 'lemma': 'θύρσις', 'pos': 'n', 'morph': '-s---fn-'}]

    """

    # Output keys are keys that are given in the end
    OUTPUT_KEYS: List[str] = ["form", "lemma", "pos", "morph"]
    # Glue dicts contains tasks that should merge together subtasks
    GLUE: Dict[str, List[str]] = {
        "morph": ["pers", "num", "tense", "mood", "voice", "gend", "case", "degree"]
    }
    # Glue_char is what is used to glue things together -> Tense=Pres|Person=1
    GLUE_CHAR: str = ""
    # Glue Empty are value to take when all things glued together are empty
    GLUE_EMPTY: Dict[str, str] = {"morph": "--------"}
    # Value that means the current element is empty
    EMPTY_TAG: Dict[str, str] = {
        "case": "-", "degree": "-", "gend": "-", "mood": "-", "num": "-",
        "pers": "-", "pos": "-", "tense": "-", "voice": "-"
    }
    KEEP_EMPTY = True

    def __init__(self, *args, **kwargs):
        super(GreekMorphProcessor, self).__init__(*args, **kwargs)

    def _get_glued(self, glued_task: str, token_dict: Dict[str, str]):
        return token_dict[glued_task]
