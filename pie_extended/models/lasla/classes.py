import sys
import regex as re
import click

try:
    import cltk
    from cltk.tokenize.word import WordTokenizer
except:
    click.echo(click.style("You need to install cltk and its Latin Data to runs this package", fg="red"))
    click.echo("pip install cltk")
    click.echo("pie-ext install-addons lasla")
    sys.exit(0)

from pie_extended.prototypes import DataIterator
from pie_extended.prototypes.formatters.glue import GlueFormatter as GenericGlueFormatter

# Uppercase regexp
uppercase = re.compile(r"^[A-Z]$")
add_space_around_punct = re.compile(r"(\s*)([^\w\s\.])(\s*)")
normalize_space = re.compile(r"(\s+)")
sentence_tokenizer = re.compile(r"([^\w\s](?:[\s\W]+)?)")


class MemoryzingTokenizer(object):
    def __init__(self):
        self.tokens = [
        ]

        self.word_tokenizer = WordTokenizer("latin")

    def sentence_tokenizer(self, data):
        sentences = list()
        first_is_dot = False
        started_writting = False  # Allows for avoiding to compute length
        for sent in sentence_tokenizer.split(data):
            sent = sent.strip()
            if sent:
                if sentence_tokenizer.match(sent):
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

    def __call__(self, data, lower=True):
        if lower:
            data = data.lower()

        # Fix regarding the current issue of apostrophe
        # https://github.com/cltk/cltk/issues/925#issuecomment-522065530
        # On the other hand, it creates empty tokens...
        data = add_space_around_punct.sub(" \g<2> ", data)
        data = normalize_space.sub(" ", data)

        for sentence in self.sentence_tokenizer(data):
            toks = self.word_tokenizer.tokenize(sentence)
            new_sentence = []

            for tok in toks:
                if tok:
                    out = self.replacer(tok)
                    self.tokens.append((len(self.tokens), tok, out))
                    new_sentence.append(out)
            if new_sentence:
                yield new_sentence


class GlueFormatter(GenericGlueFormatter):
    HEADERS = ["form", "lemma", "POS", "morph", "treated_token"]
    MORPH_PART = ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]
    PONCTU = re.compile(r"^\W+$")

    def __init__(self, tokenizer_memory):
        super(GlueFormatter, self).__init__([])
        self.tokenizer_memory = tokenizer_memory

    def rule_based(cls, token):
        if cls.PONCTU.match(token):
            return [token, token, "PUNC", "MORPH=empty", token]
        elif token.startswith("-"):
            if token == "-ne":
                lemma = "ne2"
            else:
                lemma = token[1:]
            return [token, lemma, "CONcoo", "MORPH=empty", token]

        return None


def get_iterator_and_formatter():
    tokenizer = MemoryzingTokenizer()
    formatter = GlueFormatter(tokenizer)
    iterator = DataIterator(
        tokenizer=tokenizer,
        remove_from_input=DataIterator.remove_punctuation
    )
    return iterator, formatter
