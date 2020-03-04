from typing import Dict, Generator
from pie_extended.pipeline.postprocessor.glue import GlueProcessor


class FrGlueProcessor(GlueProcessor):
    """ We glue morphological features into one column
    """
    OUTPUT_KEYS = ["form", "lemma", "POS", "morph"]
    GLUE = {"morph": ["MODE", "TEMPS", "PERS.", "NOMB.", "GENRE", "CAS"]}  # , "DEGRE"]}
    EMPTY_TAG: Dict[str, str] = {"CAS": "CAS=x", "NOMB.": "NOMB.=x", "MODE": "MODE=x", "TEMPS": "TEMPS=x",
                                 "GENRE": "GENRE=x", "PERS.": "PERS.=x"}

    # We need to change the definition of this function, because, for now,
    # the model gives us an output like
    # MODE=imp
    # and not
    # imp
    def _yield_annotation(
            self,
            token_dict: Dict[str, str]
        ) -> Generator[str, None, None]:
        # For each key we should return
        for head in self._out:
            if head not in self._glue:
                yield head, token_dict[head]
            else:
                # Otherwise, we glue together things that should be glued together
                joined = self._glue_char.join([
                    # HERE
                    # glued_task + "=" +
                    token_dict[glued_task]
                    for glued_task in self._glue[head]
                    if token_dict[glued_task] != self._empty_tags.get(glued_task, None)
                ])
                if not joined:
                    joined = self._glue_empty[head]
                yield head, joined

    def __init__(self, *args, **kwargs):
        super(FrGlueProcessor, self).__init__(*args, **kwargs)
