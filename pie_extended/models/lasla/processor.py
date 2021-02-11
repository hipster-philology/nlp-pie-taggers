import regex as re
from typing import Dict, List, Optional, Generator, Tuple

from pie_extended.pipeline.postprocessor.proto import ChainedProcessor, ProcessorPrototype
from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor
from pie_extended.utils import roman_number


class LatinRulesProcessor(RuleBasedProcessor):
    """ Lasla data has no punctuation, we tag it automatically.

    "ne" token can be two different lemma, but I don't remember why I wrote this part. (ne/nec ?)

    >>> p = LatinRulesProcessor()
    >>> p.set_tasks(["lemma", "pos", "morph", "treated"])
    ['lemma', 'pos', 'morph', 'treated']
    >>> p.get_dict("uinipollens", ['界pollens', '', '', 'uinipollens']) == [
    ...    {'lemma': 'pollens', 'treated': 'uinipollens', 'morph': 'MORPH=empty', 'pos': 'ADJqua',
    ...     'form': '{uinipollens}', 'Dis': '_'}
    ... ]
    True
    >>> p.get_dict("similist", ['界sum', '', '', 'similist']) == [{'lemma': 'sum1', 'treated': 'similist',
    ... 'morph': 'Numb=Sing|Mood=Ind|Tense=Pres|Voice=Act|Person=3',
    ... 'pos': 'VER', 'form': '{similist}', 'Dis': '_'}]
    True

    """
    PONCTU = re.compile(r"^\W+$")
    GREEK = re.compile(r"^\p{Greek}+$")
    CLITICS_POS = {
        'audeo': 'VER',
        'consultum': 'NOM',
        'cum': 'CON',
        'ientaculum': 'NOM',
        'ille': 'PROdem',
        'ipse': 'PROdem',
        'is': 'PROdem',
        'iste': 'PROdem',
        'ne': 'ADV',
        'pollens': 'ADJqua',
        'que': 'CON',
        'scribo': 'VER',
        'sum': 'VER',
        'ue': 'CON',
        'unus': '',
        'uolo': ''
    }

    CLITICS_MORPH = {
        'sum': 'Numb=Sing|Mood=Ind|Tense=Pres|Voice=Act|Person=3'
    }
    CLITICS_DIS = {
        'cum': '3',
        'ne': '2',
        'sum': '1'
    }

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        # If Else condition
        token = annotation["form"]

        if annotation["lemma"].startswith("界"):
            lem = annotation["lemma"][1:]
            return {
                "lemma": lem + self.CLITICS_DIS.get(lem, ""),
                "treated": annotation["treated"],
                "morph": self.CLITICS_MORPH.get(lem, "MORPH=empty"),
                "pos": self.CLITICS_POS.get(lem, "UNK"),
                "form": "{"+annotation["form"]+"}",
                "Dis": "_"
            }

        if self.PONCTU.match(token):
            return {"form": token, "lemma": token, "pos": "PUNC", "morph": "MORPH=empty",
                    "treated": annotation['treated'], "Dis": "_"}
        elif self.GREEK.match(token):
            return {"form": token, "lemma": "[Greek]", "pos": "FOR", "morph": "MORPH=empty",
                    "treated": annotation['treated'], "Dis": "_"}
        elif token.startswith("[IGN:"):
            return {"form": token, "lemma": "[IGNORED]", "pos": "OUT", "morph": "MORPH=empty",
                    "treated": annotation['treated'], "Dis": "_"}
        elif token.startswith("[REF:"):
            return {"form": token, "lemma": "[METADATA]", "pos": "OUT", "morph": "MORPH=empty",
                    "treated": annotation['treated'], "Dis": "_"}
        elif annotation["lemma"].isdigit() and annotation["treated"].isdigit() and not token.isnumeric():
            try:
                annotation["lemma"] = str(roman_number(token))
            except KeyError:
                annotation["lemma"] = "<UNK_NUMBER>"
                print("Weird behavior on this token", annotation)
        return annotation

    def __init__(self, *args, **kwargs):
        super(LatinRulesProcessor, self).__init__(*args, **kwargs)


class LatinGlueProcessor(GlueProcessor):
    OUTPUT_KEYS = ["form", "lemma", "pos", "morph", "Dis"]
    GLUE = {"morph": ["Case", "Numb", "Gend", "Deg", "Mood", "Tense", "Voice", "Person"]}
    WHEN_EMPTY = {"morph": "MORPH=empty"}
    EMPTY_TAG: Dict[str, str] = {"Case": "_", "Numb": "_", "Deg": "_", "Mood": "_", "Tense": "_", "Voice": "_",
                                 "Person": "_", "Gend": "_"}

    def __init__(self, *args, **kwargs):
        super(LatinGlueProcessor, self).__init__(*args, **kwargs)


class MoodTenseVoice(ChainedProcessor):
    def __init__(self, head_processor: Optional[ProcessorPrototype],
                 empty_value: str = "_", **kwargs):
        super(MoodTenseVoice, self).__init__(head_processor=head_processor)

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

