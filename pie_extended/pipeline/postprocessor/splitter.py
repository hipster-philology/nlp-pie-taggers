from typing import List, Dict, Optional
from .proto import ChainedProcessor, ProcessorPrototype


class SplitterPostProcessor(ChainedProcessor):
    """ This processor aims to help in splitting enclitics and proclitics


    >>> proc = SplitterPostProcessor()
    >>> proc.set_tasks(["lemma", "POS", "Case"])
    ['lemma', 'POS', 'Case']
    >>> proc.get_dict("praedicatione", ["praedicatio界-ne", "NOMcom", "Nominatif"]) == [
    ...    {"form": "praedicatione", "lemma": "praedicatio", "POS": "NOMcom", "Case": "Nominatif"},
    ...    {"form": "praedicatione", "lemma": "-ne", "POS": "NOMcom", "Case": "Nominatif"},
    ... ]
    True
    """

    def __init__(self, split_char: str = "界", column: str = "lemma",
                 head_processor: Optional[ProcessorPrototype] = None, **kwargs):
        super(SplitterPostProcessor, self).__init__(head_processor, **kwargs)
        self.split_char = split_char
        self.column = column

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        out = []
        for anno in super(SplitterPostProcessor, self).get_dict(token=token, tags=tags):
            if self.split_char in anno[self.column]:
                for new_val in anno[self.column].split(self.split_char):
                    out.append({
                        self.column: new_val,
                        **{x: y for x, y in anno.items() if x != self.column}
                    })
            else:
                out.append(anno)
        return out
