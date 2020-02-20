import sys
import regex as re
import click

try:
    import cltk
    from cltk.tokenize.word import WordTokenizer
except ImportError as E:
    click.echo(click.style("You need to install cltk and its Latin Data to runs this package", fg="red"))
    click.echo("pip install cltk")
    click.echo("pie-ext install-addons lasla")
    sys.exit(0)


from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.disambiguator import DisambiguatorProcessor
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from pie_extended.pipeline.postprocessor.rulebased import RuleBasedProcessor
from pie_extended.pipeline.postprocessor.glue import GlueProcessor
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer as SourceMemorizingTokenizer
from typing import Dict


class LatinRulesProcessor(RuleBasedProcessor):
    PONCTU = re.compile(r"^\W+$")

    def rules(self, annotation: Dict[str, str]) -> Dict[str, str]:
        # If Else condition
        token = annotation["form"]
        if self.PONCTU.match(token):
            return {"form": token, "lemma": token, "POS": "PUNC", "morph": "MORPH=empty"}
        elif token.startswith("-"):
            if token == "-ne":
                annotation["lemma"] = "ne2"
            else:
                annotation["lemma"] = "ne"
        return annotation


class LatinGlueProcessor(GlueProcessor):
    OUTPUT_KEYS = ["form", "lemma", "POS", "morph"]
    GLUE = {"morph": ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]}
    WHEN_EMPTY = {"morph": "MORPH=empty"}

# Uppercase regexp
uppercase = re.compile(r"^[A-Z]$")


class MemorizingTokenizer(SourceMemorizingTokenizer):

    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s\.])(\s*)")
    re_normalize_space = re.compile(r"(\s+)")
    re_sentence_tokenizer = re.compile(r"([_||[^\s\w]]+(?:[\s_||[\W]]+)?)", re.VERSION1)

    def __init__(self):
        self.tokens = [
        ]

        self._word_tokenizer = WordTokenizer("latin")

    def word_tokenizer(self, data):
        return self._word_tokenizer.tokenize(data)

    def sentence_tokenizer(self, data):
        sentences = list()
        first_is_dot = False
        started_writting = False  # Allows for avoiding to compute length
        for sent in MemorizingTokenizer.re_sentence_tokenizer.split(data):
            sent = sent.strip()
            if sent:
                if MemorizingTokenizer.re_sentence_tokenizer.match(sent):
                    if not started_writting:
                        sentences.append(sent)
                        first_is_dot = True
                    else:
                        sentences[-1] += " " + sent
                else:
                    if first_is_dot:
                        sentences[-1] += " " + sent
                        first_is_dot = False
                    else:
                        sentences.append(sent)

                if not started_writting and len(sentences):
                    started_writting = True

        yield from sentences

    def replacer(self, inp: str):
        inp = inp.replace("U", "V").replace("v", "u").replace("J", "I").replace("j", "i").lower()
        return inp

    def normalizer(self, data: str):
        # Fix regarding the current issue of apostrophe
        # https://github.com/cltk/cltk/issues/925#issuecomment-522065530
        # On the other hand, it creates empty tokens...
        data = MemorizingTokenizer.re_add_space_around_punct.sub(" \g<2> ", data)
        data = MemorizingTokenizer.re_normalize_space.sub(" ", data)
        return data


def get_iterator_and_processor():
    tokenizer = MemorizingTokenizer()
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
