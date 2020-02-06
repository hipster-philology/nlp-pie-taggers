import regex as re
from typing import List
from ...pipeline.formatters.glue import GlueFormatter as SourceGlueFormatter
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer as SourceMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator

# Uppercase regexp
_uppercase = re.compile("^[A-ZÉÈÀÂÊÎÔÛŶÄËÏÖÜŸ]$")

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"
_Dots_collections = r"[" + _Dots_except_apostrophe + "‘’]"
_RomanNumber = r"(?:M{1,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|C?D|D?C{1,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|M{0,4}" \
               r"(?:CM|CD|D?C{0,3})(?:XC|X?L|L?X{1,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|CD|D?C{0,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|I?V|V?I{1,3}))"


class MemorizingTokenizer(SourceMemorizingTokenizer):
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s\'’ʼ]+)(\s*)")
    re_add_space_after_apostrophe = re.compile(r"(\s*)([\'’ʼ])(\s*)")
    re_normalize_space = re.compile(r"(\s+)")
    re_sentence_tokenizer = re.compile(r"([_||[^\s\w]]+(?:[\s_||[\W]]+)?)", re.VERSION1)
    re_word_tokenizer = re.compile(r"[\s]+")
    _sentence_boundaries = re.compile(
        r"(?<!" + _RomanNumber + r"\.)(?<=" + _Dots_except_apostrophe + r"+)(\B)(?!\." + _RomanNumber + ")"
    )

    def __init__(self):
        self.tokens = []

    @classmethod
    def _sentence_tokenizer(cls, string: str) -> List[str]:
        string = cls._sentence_boundaries.sub(r"\g<1><SPLIT>", string)
        print(string)
        return string.split("<SPLIT>")

    def word_tokenizer(self, data):
        # ICI, il faut que tu tokenizes toi-meme avec une fonction à toi
        return data.split()

    def sentence_tokenizer(self, data):
        sentences = list()
        for sent in MemorizingTokenizer.re_sentence_tokenizer.split(data):
            sent = sent.strip()
            sentences.append(sent)
            print(sentences)
        yield from sentences

    def replacer(self, inp: str):
        inp = self.re_add_space_after_apostrophe.sub("", inp)
        return inp

    def normalizer(self, data: str):
        data = self.re_add_space_after_apostrophe.sub(
            "\g<2> ",
            self.re_add_space_around_punct.sub(" \g<2> ", data)
        )
        return data


class GlueFormatter(SourceGlueFormatter):
    HEADERS = ["form", "lemma", "POS", "morph", "treated_token"]
    MORPH_PART = ["MODE", "TEMPS", "PERS.", "NOMB.", "GENRE", "CAS", "DEGRE"]

    PONCTU = re.compile(r"^\W+$")
    NUMBER = re.compile(r"\d+")
    PONFORT = [".", "...", "!", "?"]

    def __init__(self, tokenizer_memory: MemorizingTokenizer):
        super(GlueFormatter, self).__init__(tokenizer_memory=tokenizer_memory)

    def rule_based(cls, token):
        if cls.PONCTU.match(token):
            lemma = token
            if token in GlueFormatter.PONFORT:
                pos = "PONfrt"
            else:
                pos = "PONfbl"
            return [token, lemma, pos, "MORPH=empty"]

    def format_line(self, token, tags, ignored=False):
        tags = list(tags)
        lemma = tags[self.tasks.index("lemma")]
        index, input_token, out_token = self.tokenizer_memory.tokens.pop(0)
        if token != out_token:
            raise Exception("The output token does not match our inputs %s : %s" % (token, out_token))

        overwriten = self.rule_based(token)
        if overwriten:
            return overwriten

        if type(self).NUMBER.match(token):  # This would push for sending the whole elements to rule_based and
                                            #   not the token only
            lemma = token
            tags[self.tasks.index(self.pos_tag)] = "ADJcar"

        return [
            token,
            lemma,
            tags[self.tasks.index(self.pos_tag)],
            "|".join(
                "{cat}={tag}".format(
                    cat=morph_part,
                    tag=tags[self.tasks.index(morph_part.replace(".", ""))]
                )
                for morph_part in GlueFormatter.MORPH_PART
                if morph_part.replace(".", "") in self.tasks and
                tags[self.tasks.index(morph_part.replace(".", ""))] != "_"
            ) or "MORPH=empty",
            out_token
        ]


def get_iterator_and_formatter():
    tokenizer = MemorizingTokenizer()
    formatter = GlueFormatter(tokenizer)
    iterator = DataIterator(
        tokenizer=tokenizer,
        remove_from_input=DataIterator.remove_punctuation
    )
    return iterator, formatter

