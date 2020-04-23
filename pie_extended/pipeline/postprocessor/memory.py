from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype, ChainedProcessor
from typing import Optional, Dict, List
if "typing" == "nottyping":
    from ..tokenizers.memorizing import MemorizingTokenizer


class MemoryzingProcessor(ChainedProcessor):
    """ MemoryzingProcessor proposes to keep track of changes operated on input string
    by reinserting the original data alongside a new task (KEY) where we output
    the input seen by the Model

    It reuses the memory from a class derived from MemorizingTokenizer so that it reintroduced
    the original input into the token.

    >>> from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
    >>> tokenizer = MemorizingTokenizer()
    >>> # Fake token memory : (Index, Original Input, Input seen by Tagger)
    >>> tokenizer.tokens = [(0, "A", "a"), (0, "b", "b"), (0, "q'", "q")]
    >>> processor = MemoryzingProcessor(tokenizer_memory=tokenizer, head_processor=ProcessorPrototype())
    >>> processor.set_tasks(["lem"])
    ['lem', 'treated']
    >>> # Lowercase a was taken in the input but uppercase a is returned in form. For transparency, input seen
    >>> #   By the tagger is returned in a new column, treated (cf. MemorizingProcessor.KEY)
    >>> processor.get_dict("a", ["lemma"]) == [{"form": "A", "treated": "a", "lem": "lemma"}]
    True
    >>> # Some would have the same treated and input
    >>> processor.get_dict("b", ["lemma"]) == [{"form": "b", "treated": "b", "lem": "lemma"}]
    True
    >>> # Some differ with more characters
    >>> processor.get_dict("q", ["lemma"]) == [{"form": "q'", "treated": "q", "lem": "lemma"}]
    True

    This allows for easier output alignment as well as removing unknown characters to the model. If your lemmatizer
    in training has never seen the "@" character, you can remove it at tokenization time and reinsert it with
    MemoryzingProcessor

    """
    KEY: str = "treated"

    def __init__(self, tokenizer_memory: "MemorizingTokenizer", head_processor: ProcessorPrototype,
                 key: Optional[str] = None, **kwargs):
        super(MemoryzingProcessor, self).__init__(head_processor=head_processor, **kwargs)
        self.memory: "MemorizingTokenizer" = tokenizer_memory
        self._key: str = key or type(self).KEY

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        # First we get the dictionary
        list_token_dict = []
        for token_dict in self.head_processor.get_dict(token, tags):
            index, input_token, out_token = self.memory.tokens.pop(0)
            if token != out_token:
                raise Exception("The output token does not match our inputs %s : %s" % (token, out_token))

            token_dict[self._key] = out_token
            token_dict["form"] = input_token
            list_token_dict.append(token_dict)
        return list_token_dict

    @property
    def tasks(self) -> List[str]:
        return self.head_processor.tasks + ["treated"]

    def reinsert(self, form: str) -> Dict[str, str]:
        """ Reinsert the token, should add treated to the output

        >>> from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
        >>> tokenizer = MemorizingTokenizer()
        >>> tokenizer.tokens = ["$"]
        >>> x = MemoryzingProcessor(tokenizer, ProcessorPrototype())
        >>> x.set_tasks(["task1", "task2"])
        ['task1', 'task2', 'treated']
        >>> x.reinsert("$")
        {'form': '$', 'task1': '_', 'task2': '_', 'treated': '--IGN.--'}
        """
        self.memory.tokens.pop(0)
        annotations = super(MemoryzingProcessor, self).reinsert(form)
        annotations['treated'] = '--IGN.--'
        return annotations
