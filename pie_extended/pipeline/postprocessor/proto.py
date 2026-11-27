from typing import List, Dict, Optional

DEFAULT_EMPTY = "_"


class ProcessorPrototype:
    empty_value: str

    def __init__(self, empty_value: Optional[str] = None):
        """ Applies postprocessing. Simplest Processor one could use.

        :param empty_value: Value to use to fill tasks that would not get any data


        >>> x = ProcessorPrototype(empty_value="%")
        >>> x.set_tasks(["a", "b"])
        ['a', 'b']
        >>> x.reinsert("x") == {"form": "x", "a": "%", "b": "%"}
        True
        >>> x.get_dict("y", ["1", "2"]) == [{"form": "y", "a": "1", "b": "2"}]
        True
        """
        self._tasks = []
        self.task_init: bool = False
        self.empty_value = empty_value or DEFAULT_EMPTY

    @property
    def tasks(self) -> List[str]:
        return self._tasks

    def set_tasks(self, tasks) -> List[str]:
        self.task_init = True
        self._tasks = tasks
        return tasks

    def set_spacing(self, spacing: List[bool]) -> None:
        """ Receives, for each token of the document, if it is followed by a space (only used by the
        processors that output it, see SpaceAfterProcessor) """
        pass

    def required_tasks(self, requested: List[str], available: List[str]) -> List[str]:
        """ Translates output columns into the tasks that models must produce for them

        :param requested: Output columns that are wanted
        :param available: Tasks that models can produce
        :return: Tasks (of the layer below) required to build the requested columns

        >>> ProcessorPrototype().required_tasks(["a"], ["a", "b"])
        ['a']
        """
        return list(requested)

    def reinsert(self, form: str) -> Dict[str, str]:
        """ Generates an automatic line for a token that was removed from lemmatization

        :param form: Token to reinsert
        :return: Dictionary representation of the token, as an annotation


        >>> x = ProcessorPrototype(empty_value="%")
        >>> x.set_tasks(["a", "b"])
        ['a', 'b']
        >>> x.reinsert("x") == {"form": "x", "a": "%", "b": "%"}
        True
        """
        return dict(form=form, **{task: self.empty_value for task in self._tasks})

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        """ Get the dictionary representation of a token annotation

        :param token: Token used as input for pie
        :param tags: List of tags generated
        :return: Dictionary representation of the token and its annotations

        >>> x = ProcessorPrototype(empty_value="%")
        >>> x.set_tasks(["a", "b"])
        ['a', 'b']
        >>> x.get_dict("y", ["1", "2"]) == [{"form": "y", "a": "1", "b": "2"}]
        True
        """
        return [{"form": token, **{k: val for k, val in zip(self._tasks, tags)}}]

    def reset(self):
        """ Functions that should be run in between documents

        >>> x = ProcessorPrototype(empty_value="%")
        >>> x.set_tasks(["a", "b"])
        ['a', 'b']
        >>> x.reset()
        """
        pass


class RenamedTaskProcessor(ProcessorPrototype):
    def __init__(self, task_map: Dict[str, str], **kwargs):
        """ This Processor is used for renaming tasks (Pie for example refuses tasks containing dots)

        >>> x = RenamedTaskProcessor({"task_name_1": "renamed"})
        >>> x.set_tasks(["task_name_1", "y"])
        ['renamed', 'y']
        >>> x.get_dict("token", ["a", "b"]) == [{"form": "token", "renamed": "a", "y": "b"}]
        True
        """
        super(RenamedTaskProcessor, self).__init__(**kwargs)
        self._map: Dict[str, str] = task_map

    def set_tasks(self, tasks):
        self._tasks = [self._map.get(task, task) for task in tasks]
        return self.tasks

    def required_tasks(self, requested: List[str], available: List[str]) -> List[str]:
        """ Inverts the renaming

        >>> RenamedTaskProcessor({"pos": "POS"}).required_tasks(["POS", "lemma"], ["pos", "lemma"])
        ['pos', 'lemma']
        """
        inverse = {new: old for old, new in self._map.items()}
        # A task is only inverted if the model really owns the original name
        return [inverse[task] if task in inverse and inverse[task] in available else task for task in requested]


class ChainedProcessor(ProcessorPrototype):
    """ Allows for easy chaining !

    The ChainedProcessor is basically using its headprocessor in the background and checking it's output to some extent

    The prototype of ChainedProcessor using Processor Prototype would have the same results because
    chained processor is not doing anything new except enabling chaining

        >>> x = ProcessorPrototype(empty_value="%")
        >>> x.set_tasks(["a", "b"])
        ['a', 'b']
        >>> y = ChainedProcessor(x)
        >>> y.set_tasks(["a", "b"])
        ['a', 'b']
        >>> x.reinsert("x") == y.reinsert("x")
        True
        >>> x.get_dict("y", ["1", "2"]) == y.get_dict("y", ["1", "2"])
        True

    You can subclass it to modify the output of the preceding processor :

    >>> class ExampleChained(ChainedProcessor):
    ...     def reinsert(self, form: str) -> Dict[str, str]:
    ...         annotation = self.head_processor.reinsert(form)
    ...         annotation["col3"] = "x"
    ...         return annotation
    ...
    ...     def get_dict(self, form: str, tags: List[str]) -> List[Dict[str, str]]:
    ...         return [{"col3": "x", **{x:y for x, y in anno.items() if x != "col3"}}
    ...                  for anno in self.head_processor.get_dict(form, tags)]
    >>> x = ExampleChained(ProcessorPrototype(empty_value="EMPTY"))
    >>> x.set_tasks(["a", "b"])
    ['a', 'b']
    >>> x.reinsert("x") == {"form": "x", "a": "EMPTY", "b": "EMPTY", "col3": "x"}
    True
    >>> x.get_dict("y", ["1", "2"]) == [{"form": "y", "a": "1", "b": "2", "col3": "x"}]
    True

    """
    head_processor: ProcessorPrototype

    def __init__(self, head_processor: Optional[ProcessorPrototype], **kwargs):
        super(ChainedProcessor, self).__init__(**kwargs)

        self.head_processor: ProcessorPrototype = head_processor
        if not self.head_processor:
            self.head_processor = ProcessorPrototype()

    def set_tasks(self, tasks):
        self._tasks = self.head_processor.set_tasks(tasks)
        return self.tasks

    def reinsert(self, form: str) -> Dict[str, str]:
        return self.head_processor.reinsert(form)

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        return self.head_processor.get_dict(token, tags)

    def required_tasks(self, requested: List[str], available: List[str]) -> List[str]:
        return self.head_processor.required_tasks(requested, available)

    def reset(self):
        self.head_processor.reset()


class SelectTasksProcessor(ChainedProcessor):
    """ Restricts the output columns to a subset of the tasks.

    Useful when a processor needs hidden dependencies (e.g. a lemma to split clitics) that
    were not asked for by the user.

    >>> x = SelectTasksProcessor(ProcessorPrototype(), ["b"])
    >>> x.set_tasks(["a", "b"])
    ['b']
    >>> x.get_dict("y", ["1", "2"])[0]["b"]
    '2'
    """
    def __init__(self, head_processor: Optional[ProcessorPrototype], selected: List[str], **kwargs):
        super(SelectTasksProcessor, self).__init__(head_processor, **kwargs)
        self.selected: List[str] = list(selected)

    def set_tasks(self, tasks):
        self.head_processor.set_tasks(tasks)
        self.task_init = True
        self._tasks = [task for task in self.head_processor.tasks if task in self.selected]
        return self._tasks

    @property
    def tasks(self) -> List[str]:
        return self._tasks
