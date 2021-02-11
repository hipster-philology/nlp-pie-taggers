from pie_extended.pipeline.postprocessor.proto import ChainedProcessor, ProcessorPrototype, RenamedTaskProcessor
from typing import Generator, Dict, List


class GlueProcessor(ChainedProcessor):
    """ Glues together specific tasks

    >>> class SimpleGlue(GlueProcessor):
    ...     OUTPUT_KEYS = ["form", "lemma", "task3"]
    ...     GLUE = {"task3": ["1", "2"]} # Merges Task `1` output and task `2` output in `task3`
    ...     EMPTY_TAG = {"1": "_", "2": "_"} # If _ is tagged in task `1`, it's the same as an empty tag
    ...     GLUE_EMPTY = {"task3": "NO-DATA"}  # When all merged data are empty, default value
    >>> x = SimpleGlue(head_processor=ProcessorPrototype())
    >>> x.set_tasks(["lemma", "1", "2"]) # You can see things are remaped
    ['lemma', 'task3']
    >>> # Merges b and c values from task 1 and 2 into a new task
    >>> x.get_dict("a", ["a", "b", "c"]) == [{"form": "a", "lemma": "a", "task3": "1=b|2=c"}]
    True
    >>> # Keeps only one task because 2 is empty
    >>> x.get_dict("a", ["a", "b", "_"]) == [{"form": "a", "lemma": "a", "task3": "1=b"}]
    True
    >>> # Fills with the default empty tag because both task 1 and 2 were empty
    >>> x.get_dict("a", ["a", "_", "_"]) == [{"form": "a", "lemma": "a", "task3": "NO-DATA"}]
    True

    You can also use remaped tasks:

    >>> class AnotherGlue(GlueProcessor):
    ...     OUTPUT_KEYS = ["form", "lemma", "POS", "task3"]
    ...     GLUE = {"task3": ["1", "2"]} # Merges Task `1` output and task `2` output in `task3`
    ...     EMPTY_TAG = {"1": "_", "2": "_"} # If _ is tagged in task `1`, it's the same as an empty tag
    ...     GLUE_EMPTY = {"task3": "NO-DATA"}  # When all merged data are empty, default value
    >>> x = AnotherGlue(head_processor=RenamedTaskProcessor({"pos": "POS"}))
    >>> x.set_tasks(["lemma", "pos", "1", "2"]) # You can see things are remaped
    ['lemma', 'POS', 'task3']
    >>> # Merges b and c values from task 1 and 2 into a new task
    >>> x.get_dict("a", ["a", "p", "b", "c"])
    [{'form': 'a', 'lemma': 'a', 'POS': 'p', 'task3': '1=b|2=c'}]

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
    KEEP_EMPTY = False

    def __init__(self, *args, **kwargs):
        super(GlueProcessor, self).__init__(*args, **kwargs)

        # Sets-up some copy of the values
        self._out = self.OUTPUT_KEYS
        self._glue = self.GLUE
        self._glue_char = self.GLUE_CHAR
        self._glue_empty = self.GLUE_EMPTY
        self._empty_tags = self.EMPTY_TAG
        self._keep_empty = self.KEEP_EMPTY

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
                    self._get_glued(glued_task, token_dict)
                    for glued_task in self._glue[head]
                    if self._keep_empty or token_dict[glued_task] != self._empty_tags.get(glued_task, None)
                ])
                if not joined:
                    joined = self._glue_empty[head]
                yield head, joined

    def _get_glued(self, glued_task: str, token_dict: Dict[str, str]):
        return glued_task + "=" + token_dict[glued_task]

    def reinsert(self, form: str) -> Dict[str, str]:
        return dict(form=form, **{key: self.empty_value for key in self._out if key != "form"})

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        return [dict(self._yield_annotation(as_dict)) for as_dict in super(GlueProcessor, self).get_dict(token, tags)]

    @property
    def tasks(self) -> List[str]:
        return [key for key in self._out if key != "form"]
