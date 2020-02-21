from .proto import ProcessorPrototype, ChainedProcessor
from typing import Optional, Dict, List
if "typing" == "nottyping":
    from ..tokenizers.memorizing import MemorizingTokenizer


class RuleBasedProcessor(ChainedProcessor):
    """ Applies rules found in rules(token_annotation)

    """
    KEY: str = "treated"

    def __init__(self, apply_on_reinsert: bool = False, head_processor: Optional[ProcessorPrototype] = None, **kwargs):
        """ Apply rules on output of the taggers

        :param apply_on_reinsert: Apply rules on reinsert task
        """
        super(RuleBasedProcessor, self).__init__(head_processor=head_processor, **kwargs)
        self._key: str = type(self).KEY
        self.apply_on_reinsert= apply_on_reinsert

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        return annotation

    def reinsert(self, form: str) -> Dict[str, str]:
        anno = super(RuleBasedProcessor, self).reinsert(form)
        if self.apply_on_reinsert:
            return self.rules(anno)
        return anno

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        return self.rules(self.head_processor.get_dict(token, tags))