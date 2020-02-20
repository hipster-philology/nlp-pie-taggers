from .proto import ProcessorPrototype, ChainedProcessor
from typing import Optional, Dict, List
if "typing" == "nottyping":
    from ..tokenizers.memorizing import MemorizingTokenizer


class RuleBasedProcessor(ChainedProcessor):
    """ Applies rules found in rules(token_annotation)

    """
    KEY: str = "treated"

    def __init__(self, head_processor: Optional[ProcessorPrototype], **kwargs):
        super(RuleBasedProcessor, self).__init__(head_processor=head_processor, **kwargs)
        self._key: str = type(self).KEY

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        return annotation

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        return self.rules(self.head_processor.get_dict(token, tags))