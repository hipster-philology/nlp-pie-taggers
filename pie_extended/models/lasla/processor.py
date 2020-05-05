import regex as re
from typing import Dict, List, Optional, Generator, Tuple

from pie_extended.pipeline.postprocessor.proto import ChainedProcessor, ProcessorPrototype
from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor


class LatinRulesProcessor(RuleBasedProcessor):
    """ Lasla data has no punctuation, we tag it automatically.

    "ne" token can be two different lemma, but I don't remember why I wrote this part. (ne/nec ?)

    """
    PONCTU = re.compile(r"^\W+$")

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        # If Else condition
        token = annotation["form"]

        if self.PONCTU.match(token):
            return {"form": token, "lemma": token, "pos": "PUNC", "morph": "MORPH=empty",
                    "treated": annotation['treated']}
        elif token.startswith("-"):
            if token == "-ne":
                annotation["lemma"] = "ne2"
            else:
                annotation["lemma"] = "ne"
        return annotation

    def __init__(self, *args, **kwargs):
        super(LatinRulesProcessor, self).__init__(*args, **kwargs)


class LatinGlueProcessor(GlueProcessor):
    OUTPUT_KEYS = ["form", "lemma", "pos", "morph"]
    GLUE = {"morph": ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]}
    WHEN_EMPTY = {"morph": "MORPH=empty"}

    def __init__(self, *args, **kwargs):
        super(LatinGlueProcessor, self).__init__(*args, **kwargs)


class Mood_Tense_Voice(ChainedProcessor):
    def __init__(self, head_processor: Optional[ProcessorPrototype],
                 empty_value: str = "_", **kwargs):
        super(ChainedProcessor, self).__init__(**kwargs)

        self.head_processor: ProcessorPrototype = head_processor
        if not self.head_processor:
            self.head_processor = ProcessorPrototype()
        self._out_tasks = []
        self.empty_value = empty_value

    def set_tasks(self, tasks):
        self._tasks = self.head_processor.set_tasks(tasks)
        self._out_tasks = [
            subtask
            for task in self._tasks
            for subtask in task.split("_")
        ]
        return self.tasks

    def reinsert(self, form: str) -> Dict[str, str]:
        return dict(form=form, **{key: self.empty_value for key in self._out_tasks if key != "form"})

    def _yield_key(self, dic: Dict[str, str]) -> Generator[Tuple[str, str], None, None]:
        for key, value in dic.items():
            if "_" in key:
                keys, values = key.split("_"), value.split("|")
                for k, v in zip(keys, values+[self.empty_value]*(len(keys)-len(values))):
                    yield k, v
            else:
                yield key, value

    def get_dict(self, token: str, tags: List[str]) -> List[Dict[str, str]]:
        return [
            dict(self._yield_key(dic))
            for dic in self.head_processor.get_dict(token, tags)
        ]

    def reset(self):
        self.head_processor.reset()

