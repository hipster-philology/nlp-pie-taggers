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
        super(MemorizingTokenizer, self).__init__(
            sentence_tokenizer=self._sentence_tokenizer,
            word_tokenizer=self._word_tokenizer,
            normalizer=self._normalizer
        )
        self.tokens = []

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

    @staticmethod
    def _word_tokenizer(data):
        # ICI, il faut que tu tokenizes toi-meme avec une fonction à toi
        return data.split()

    def _sentence_tokenizer(self, data):
        sentences = list()
        data = self.normalizer(data)
        for sent in self._real_sentence_tokenizer(data):
            sent = sent.strip()
            if sent:
                sentences.append(sent)
        yield from sentences

    def _replacer(self, inp: str):
        out = self.re_remove_ending_apostrophe.sub("", inp)
        return out

    def _normalizer(self, data: str):
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
            return [token, lemma, pos, "MORPH=empty", token]

    def format_line(self, token, tags, ignored=False):
        tags = list(tags)
        lemma = tags[self.tasks.index("lemma")]
        index, input_token, out_token = self.tokenizer_memory.tokens.pop(0)

        if token != out_token:
            raise Exception("The output token does not match our inputs %s : %s" % (token, out_token))

        overwriten = self.rule_based(out_token)

        if overwriten:
            return overwriten

        if type(self).NUMBER.match(token):  # This would push for sending the whole elements to rule_based and
                                            #   not the token only
            lemma = token
            tags[self.tasks.index(self.pos_tag)] = "ADJcar"

        return [
            input_token,
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

