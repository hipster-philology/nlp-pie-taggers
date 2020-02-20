from ..disambiguators.proto import Disambiguator
from .proto import ProcessorPrototype, ChainedProcessor
from typing import Optional, Dict, List


# Right now disambiguation is applied at the sentence level. Question is should we ?
# Keeping that here for the moment

class DisambiguatorProcessor(ChainedProcessor):
    """ Applies rules found in rules(token_annotation)

    """

    def __init__(self, disambiguator: Disambiguator, head_processor: Optional[ProcessorPrototype], **kwargs):
        super(DisambiguatorProcessor, self).__init__(head_processor=head_processor, **kwargs)
        self.disambiguator: Disambiguator = disambiguator

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        return annotation

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        return self.rules(self.head_processor.get_dict(token, tags))