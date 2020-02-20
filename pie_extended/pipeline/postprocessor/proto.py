from typing import List, Dict, Optional, Type

DEFAULT_EMPTY = "_"


class ProcessorPrototype:
    tasks: List[str]
    empty_value: str

    def __init__(self, empty_value: Optional[str] = None):
        self.tasks = []
        self.empty_value = empty_value or DEFAULT_EMPTY

    def set_tasks(self, tasks):
        self.tasks = tasks

    def postprocess(self, line):
        pass

    def reinsert(self, form: str) -> Dict[str, str]:
        """ Generates an automatic line for a token that was removed from lemmatization

        :param form: Token to reinsert
        :return: Dictionary representation of the token, as an annotation
        """
        return dict(form=form, **{task: self.empty_value for task in self.tasks})

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        """ Get the dictionary representation of a token annotation

        :param token:
        :param tags:
        :return:
        """
        return dict(form=token, **dict(zip(self.tasks, tags)))

    def reset(self):
        """ Functions that should be run in between documents """
        pass


class RenamedTaskProcessor(ProcessorPrototype):
    MAP: Dict[str, str]

    def __init__(self, **kwargs):
        super(RenamedTaskProcessor, self).__init__(**kwargs)
        self._map: Dict[str, str] = type(self).MAP

    def set_tasks(self, tasks):
        return [self._map.get(task, task) for task in tasks]


class ChainedProcessor(ProcessorPrototype):
    """ Allows for easy chaining !

    ChainedProcessor(ProcessorPrototype) basically should behave like a normal processor

    """
    head_processor: ProcessorPrototype

    def __init__(self, head_processor: Optional[ProcessorPrototype], **kwargs):
        super(ChainedProcessor, self).__init__(**kwargs)

        self.head_processor: ProcessorPrototype = head_processor
        if not self.head_processor:
            self.head_processor = ProcessorPrototype()

    def set_tasks(self, tasks):
        super(ChainedProcessor, self).set_tasks(tasks)
        self.head_processor.set_tasks(tasks)

    def reinsert(self, form: str) -> Dict[str, str]:
        return self.head_processor.reinsert(form)

    def get_dict(self, token: str, tags: List[str]) -> Dict[str, str]:
        return self.head_processor.get_dict(token, tags)

    def reset(self):
        self.head_processor.reset()