from typing import List, Tuple, Optional
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.tagger import ExtensibleTagger
from pie.utils import model_spec
from pie_extended.cli.utils import get_imports


class FakeTagger(ExtensibleTagger):
    def __init__(self, tokens, tasks):
        self.tokens = tokens
        self.tasks = tasks
        self.seen = []
        self.lower = False
        self.batch_size = 100
        self.disambiguation = None

    def tag(self, sents, **kwargs):
        self.seen.extend(sents)

        return self.tokens, self.tasks


class FakeAutoTag(ExtensibleTagger):
    def __init__(self, tasks: List[str], **kwargs):
        self.tokens: List[str] = []
        self.lengths: List[int] = []
        self.tasks = tasks
        self.lower = False
        self.glue_task: str = kwargs.get("glue_task", "_")
        self.glue_value: str = kwargs.get("glue_value", "|")
        self.disambiguation = None
        self.start_end: bool = False
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def toggle_start_end(self, status: Optional[bool] = None) -> bool:
        if status is None:
            self.start_end = not self.start_end
        else:
            self.start_end = status
        return self.start_end

    def tag(self, sents: List[List[str]], lengths: List[int], *args, **kwargs):
        """ Fake tagging tokens by enumerating informations

        >>> tagger = FakeAutoTag(["pos", "lemma"])
        >>> tagger.tag([['a', 'b'], ['c']], lengths=[2, 1])
        ([[('a', ('pos0', 'lemma0')), ('b', ('pos1', 'lemma1'))], [('c', ('pos2', 'lemma2'))]], ['pos', 'lemma'])

        """
        self.tokens.extend(list(sents))
        self.lengths.extend(lengths)

        for t, l in zip(sents, lengths):
            if len(t) != l:
                raise ValueError("Tokens and lengths are inequal [len({}) != {}]".format(str(t), l))

        out = []
        total = 0

        def get_task(task, i):
            if "_" in task:
                return self.glue_value.join([tsk+str(i) for tsk in task.split(self.glue_task)])
            return task+str(i)

        for sent in sents:
            out.append([])
            if self.start_end:
                out[-1].append(("START", tuple(list(get_task(task, total) for task in self.tasks))))
            for tok in sent:
                out[-1].append((tok, tuple(list(get_task(task, total) for task in self.tasks))))
                total += 1
            if self.start_end:
                out[-1].append(("END", tuple(list(get_task(task, total) for task in self.tasks))))
        return out, self.tasks

    @staticmethod
    def from_model_string(model_string: str, **kwargs) -> "FakeAutoTag":
        """

        :param model_string:
        :return:

        >>> tagger = FakeAutoTag.from_model_string("<path/to/tar,MODE,TEMPS,PERS,NOMB><path/to/tar,lemma,pos>")
        >>> tagger.tasks
        ['MODE', 'TEMPS', 'PERS', 'NOMB', 'lemma', 'pos']
        """
        return FakeAutoTag(tasks=[
            task
            for _, tasks in model_spec(model_string)
            for task in tasks
        ], **kwargs)


def create_auto_tagger(module, **kwargs) -> Tuple[FakeAutoTag, DataIterator, ProcessorPrototype]:
    """ Create a tagger as well as the iterator """
    tagger = FakeAutoTag.from_model_string(module.Models, batch_size=16, **kwargs)
    imports = get_imports(module)
    disambiguator = getattr(imports, "Disambiguator", None)
    if hasattr(disambiguator, "create"):
        disambiguator = disambiguator.create()
    tagger.disambiguation = disambiguator

    iterator, processor = imports.get_iterator_and_processor()
    return tagger, iterator, processor
