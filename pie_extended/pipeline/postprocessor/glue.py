from .proto import ProcessorPrototype, RenamedTaskProcessor
from typing import Generator, Dict, List


class GlueProcessor(RenamedTaskProcessor):
    """ Glues together specific tasks

    """

    # Output keys are keys that are given in the end
    OUTPUT_KEYS: List[str] = ["form", "lemma", "POS", "morph"]
    # Glue dicts contains tasks that should merge together subtasks
    GLUE: Dict[str, List[str]] = {"morph": ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]}
    # Glue_char is what is used to glue things together -> Tense=Pres|Person=1
    GLUE_CHAR: str = "|"
    # Glue Empty are value to take when all things glued together are empty
    GLUE_EMPTY: Dict[str, str] = {"morph": "MORPH=empty"}
    # Value that means the current element is empty
    EMPTY_TAG: Dict[str, str] = {"Case": "_", "Numb": "_", "Deg": "_", "Mood": "_", "Tense": "_", "Voice": "_",
                                 "Person": "_"}

    def __init__(self, *args, **kwargs):
        super(GlueProcessor, self).__init__(*args, **kwargs)

        # Sets-up some copy of the values
        self._out = self.OUTPUT_KEYS
        self._glue = self.GLUE
        self._glue_char = self.GLUE_CHAR
        self._glue_empty = self.GLUE_EMPTY
        self._empty_tags = self.EMPTY_TAG

    def set_tasks(self, tasks):
        super(GlueProcessor, self).set_tasks(tasks)

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
                    glued_task + "=" + token_dict[glued_task]
                    for glued_task in self._glue[head]
                    if token_dict[glued_task] != self._empty_tags.get(glued_task, -1)
                ])
                if not joined:
                    joined = self._glue_empty[head]
                yield head, joined

    def reinsert(self, form: str) -> Dict[str, str]:
        return dict(form=form, **{key: self.empty_value for key in self._out if key != "form"})

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        as_dict = super(GlueProcessor, self).get_dict(token, tags)
        return dict(self._yield_annotation(as_dict))
