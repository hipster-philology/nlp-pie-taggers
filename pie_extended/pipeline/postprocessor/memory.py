from .proto import ProcessorPrototype, ChainedProcessor
from typing import Optional, Dict, List
if "typing" == "nottyping":
    from ..tokenizers.memorizing import MemorizingTokenizer


class MemoryzingProcessor(ChainedProcessor):
    """ MemoryzingProcessor proposes to keep track of changes operated on input string
    by reinserting the original data alongside a new task (KEY) where we output
    the input seen by the Model

    """
    KEY: str = "treated"

    def __init__(self, tokenizer_memory: "MemorizingTokenizer", head_processor: Optional[ProcessorPrototype], **kwargs):
        super(MemoryzingProcessor, self).__init__(head_processor=head_processor, **kwargs)
        self.memory: "MemorizingTokenizer" = tokenizer_memory
        self._key: str = type(self).KEY

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        # First we get the dictionary
        token_dict = self.head_processor.get_dict(token, tags)
        index, input_token, out_token = self.memory.tokens.pop(0)
        if token != out_token:
            raise Exception("The output token does not match our inputs %s : %s" % (token, out_token))

        token_dict[self._key] = out_token
        token_dict["form"] = input_token
        return token_dict

    def reinsert(self, form: str) -> Dict[str, str]:
        self.memory.tokens.pop(0)
        return super(MemoryzingProcessor, self).reinsert(form)
