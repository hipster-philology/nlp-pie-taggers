from typing import Dict, List, Optional

from .proto import ChainedProcessor, ProcessorPrototype


class SpaceAfterProcessor(ChainedProcessor):
    """ Adds a column telling if a token is followed by a space in the original text (CoNLL-U `SpaceAfter`).

    The value is `No` when the next token is glued to this one, and the empty value (`_`) otherwise.

    It has to be the outermost processor: it is called once per input token (either with `get_dict` or with
    `reinsert`, in the order of the text), whatever the number of annotations the processors below generate.
    When a token is split in several annotations (clitics, for example), all of them but the last one are
    glued to the next one.

    >>> processor = SpaceAfterProcessor(ProcessorPrototype())
    >>> processor.set_tasks(["lemma"])
    ['lemma', 'SpaceAfter']
    >>> processor.set_spacing([False, True, True])
    >>> processor.get_dict("virumque", ["uir"]) == [{"form": "virumque", "lemma": "uir", "SpaceAfter": "No"}]
    True
    >>> processor.reinsert(":") == {"form": ":", "lemma": "_", "SpaceAfter": "_"}
    True
    >>> processor.get_dict("cano", ["cano"]) == [{"form": "cano", "lemma": "cano", "SpaceAfter": "_"}]
    True

    The consumed values are forgotten at reset (between documents):

    >>> processor.reset()
    >>> processor.get_dict("cano", ["cano"])[0]["SpaceAfter"]
    '_'
    """
    KEY: str = "SpaceAfter"
    NO_SPACE: str = "No"
    # Tells the tagger it should compute the spacing before tagging
    needs_spacing: bool = True

    def __init__(self, head_processor: Optional[ProcessorPrototype], **kwargs):
        super(SpaceAfterProcessor, self).__init__(head_processor, **kwargs)
        self._spacing: List[bool] = []
        self._cursor: int = 0

    @property
    def tasks(self) -> List[str]:
        return self.head_processor.tasks + [self.KEY]

    def set_spacing(self, spacing: List[bool]) -> None:
        """ Gives, for each token of the document, if it is followed by a space """
        self._spacing = list(spacing)
        self._cursor = 0

    def _next(self) -> str:
        if self._cursor < len(self._spacing):
            has_space = self._spacing[self._cursor]
        else:
            has_space = True
        self._cursor += 1
        return self.empty_value if has_space else self.NO_SPACE

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        annotations = self.head_processor.get_dict(token, tags)
        value = self._next()
        for annotation in annotations[:-1]:
            annotation[self.KEY] = self.NO_SPACE
        for annotation in annotations[-1:]:
            annotation[self.KEY] = value
        return annotations

    def reinsert(self, form: str) -> Dict[str, str]:
        annotation = self.head_processor.reinsert(form)
        annotation[self.KEY] = self._next()
        return annotation

    def reset(self):
        self._spacing = []
        self._cursor = 0
        super(SpaceAfterProcessor, self).reset()
