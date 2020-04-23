from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype, ChainedProcessor
from typing import Optional, Dict, List
if "typing" == "nottyping":
    from ..tokenizers.memorizing import MemorizingTokenizer


class RuleBasedProcessor(ChainedProcessor):
    """ Applies rules found in rules(token_annotation)

    """

    def __init__(self, apply_on_reinsert: bool = False, head_processor: Optional[ProcessorPrototype] = None, **kwargs):
        """ Apply rules on output of the taggers

        :param apply_on_reinsert: Apply rules on reinsert task
        :param head_processor: Processor to use before post-processing its results

        >>> class ExampleRule(RuleBasedProcessor):
        ...     def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        ...         if annotation["form"] == "need":
        ...             annotation["1"] = "REPLACED"
        ...         return annotation
        >>> processor = ExampleRule()
        >>> processor.set_tasks(["1", "2"])
        ['1', '2']
        >>> processor.get_dict("token", ["a", "b"]) == [{"form": "token", "1": "a", "2": "b"}]
        True
        >>> processor.get_dict("need", ["a", "b"]) == [{"form": "need", "1": "REPLACED", "2": "b"}]
        True
        """
        super(RuleBasedProcessor, self).__init__(head_processor=head_processor, **kwargs)
        self.apply_on_reinsert = apply_on_reinsert

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        return annotation

    def reinsert(self, form: str) -> Dict[str, str]:
        anno = super(RuleBasedProcessor, self).reinsert(form)
        if self.apply_on_reinsert:
            return self.rules(anno)
        return anno

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        return [self.rules(anno) for anno in self.head_processor.get_dict(token, tags)]
