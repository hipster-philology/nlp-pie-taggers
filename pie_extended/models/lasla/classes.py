from typing import Dict, List, Generator
import sys
import regex as re
import click
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor
from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.models.fro.classes import _RomanNumber, _Dots_except_apostrophe, _Dots_collections

try:
    import cltk
    from cltk.tokenize.word import WordTokenizer
except ImportError as E:
    click.echo(click.style("You need to install cltk and its Latin Data to runs this package", fg="red"))
    click.echo("pip install cltk")
    click.echo("pie-ext install-addons lasla")
    sys.exit(0)


class LatinRulesProcessor(RuleBasedProcessor):
    """ Lasla data has no punctuation, we tag it automatically.

    "ne" token can be two different lemma, but I don't remember why I wrote this part. (ne/nec ?)

    """
    PONCTU = re.compile(r"^\W+$")

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        # If Else condition
        token = annotation["form"]
        if self.PONCTU.match(token):
            return {"form": token, "lemma": token, "pos": "PUNC", "morph": "MORPH=empty"}
        elif token.startswith("-"):
            if token == "-ne":
                annotation["lemma"] = "ne2"
            else:
                annotation["lemma"] = "ne"
        return annotation

    def __init__(self, *args, **kwargs):
        super(LatinRulesProcessor, self).__init__(*args, **kwargs)


class LatinGlueProcessor(GlueProcessor):
    OUTPUT_KEYS = ["form", "lemma", "POS", "morph"]
    GLUE = {"morph": ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]}
    WHEN_EMPTY = {"morph": "MORPH=empty"}
    MAP = {"pos": "POS"}

    def __init__(self, *args, **kwargs):
        super(LatinGlueProcessor, self).__init__(*args, **kwargs)


# Uppercase regexp
uppercase = re.compile(r"^[A-Z]$")


class LatMemorizingTokenizer(MemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)(\.+[^\w\s\'’ʼ])(\s*)")
    re_add_space_around_apostrophe_that_are_quotes = re.compile(
        r"((((?<=[\W])[\'’ʼ]+(?=[\W]))|((?<=[\w])[\'’ʼ]+(?=[\W]))|((?<=[\W])[\'’ʼ]+(?=[\w]))))"
        # NotLetter+Apo+NotLetter or Letter+Apo+NotLetter or NotLetter+Apo+Letter
        # ?'. or manger'_ or _'Bonjour
    )
    re_add_space_after_apostrophe = re.compile(r"(\s*)([\'’ʼ])(\s*)")
    re_remove_ending_apostrophe = re.compile(r"(?<=\w)([\'’ʼ])")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    roman_number_dot = re.compile(r"\.(" + _RomanNumber + r")\.")

    def __init__(self):
        super(LatMemorizingTokenizer, self).__init__()
        self.tokens = []
        self._word_tokenizer = WordTokenizer("latin")

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    @classmethod
    def _real_sentence_tokenizer(cls, string: str) -> List[str]:
        string = cls._sentence_boundaries.sub(cls._sentence_tokenizer_merge_matches, string)
        string = string.replace("_DOT_", ".")
        return string.split("<SPLIT>")

    def _real_word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        tokenized = [tok for tok in self._word_tokenizer.tokenize(text) if tok]
        if tokenized:
            tokenized = [tok.lower() for tok in tokenized]
        return tokenized

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        sentences = list()
        data = self.normalizer(text)
        for sent in self._real_sentence_tokenizer(data):
            sent = sent.strip()
            if sent:
                sentences.append(self.word_tokenizer(sent))
        yield from sentences

    def normalizer(self, data: str) -> str:
        data = self.re_remove_ending_apostrophe.sub(
            r"\g<1> ",
            self.re_add_space_around_apostrophe_that_are_quotes.sub(
                r" \g<2> ",
                self.re_add_space_around_punct.sub(
                    r" \g<2> ",
                    self.roman_number_dot.sub(
                        r"_DOT_\g<1>_DOT_",
                        data
                    )
                )
            )
        )
        return data

    def replacer(self, inp: str):
        inp = inp.replace("V", "U").replace("v", "u").replace("J", "I").replace("j", "i")
        return inp

    #def normalizer(self, data: str):
    #    # Fix regarding the current issue of apostrophe
    #    # https://github.com/cltk/cltk/issues/925#issuecomment-522065530
    #    # On the other hand, it creates empty tokens...
    #    data = MemorizingTokenizer.re_add_space_around_punct.sub(" \g<2> ", data)
    #    data = MemorizingTokenizer.re_normalize_space.sub(" ", data)
    #    return data


def get_iterator_and_processor():
    tokenizer = LatMemorizingTokenizer()
    processor = LatinRulesProcessor(
        MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=LatinGlueProcessor()
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        remove_from_input=DataIterator.remove_punctuation
    )
    return iterator, processor
