from typing import List, Dict, Optional
from .proto import ChainedProcessor, ProcessorPrototype
from copy import deepcopy


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

    `keep=True` can be used with something like a RuleBased tokenizer to detect beforehand clitics
    and treat the tokens for example with RuleBased on top of it (len(get_dict()) > 1)

    >>> proc = SplitterPostProcessor(keep=True)
    >>> proc.set_tasks(["lemma", "POS", "Case"])
    ['lemma', 'POS', 'Case']
    >>> proc.get_dict("praedicatione", ["praedicatio界-ne", "NOMcom", "Nominatif"]) == [
    ...    {"form": "praedicatione", "lemma": "praedicatio界-ne", "POS": "NOMcom", "Case": "Nominatif"},
    ...    {"form": "praedicatione", "lemma": "praedicatio界-ne", "POS": "NOMcom", "Case": "Nominatif"}
    ... ]
    True
    >>> proc = SplitterPostProcessor(keep=False, prefix="界")
    >>> proc.set_tasks(["lemma", "POS", "Case"])
    ['lemma', 'POS', 'Case']
    >>> proc.get_dict("praedicatione", ["praedicatio界ne", "NOMcom", "Nominatif"]) ==  [
    ...    {"form": "praedicatione", "lemma": "praedicatio", "POS": "NOMcom", "Case": "Nominatif"},
    ...    {"form": "praedicatione", "lemma": "界ne", "POS": "NOMcom", "Case": "Nominatif"}
    ... ]
    True
    """

    def __init__(self, split_char: str = "界", column: str = "lemma", keep: bool = False,
                 head_processor: Optional[ProcessorPrototype] = None, prefix: str = "", **kwargs):
        super(SplitterPostProcessor, self).__init__(head_processor, **kwargs)
        self.split_char: str = split_char
        self.column: str = column
        self.keep: bool = keep
        self.prefix: str = prefix

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        out = []
        for anno in super(SplitterPostProcessor, self).get_dict(token=token, tags=tags):
            if self.split_char in anno[self.column]:
                for number, new_val in enumerate(anno[self.column].split(self.split_char)):
                    if number > 0:
                        new_val = self.prefix + new_val
                    if self.keep:
                        out.append(anno)
                    else:
                        new = deepcopy(anno)
                        new[self.column] = new_val
                        out.append(new)
            else:
                out.append(anno)
        return out
