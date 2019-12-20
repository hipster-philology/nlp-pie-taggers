import regex as re
from ...pipeline.formatters.glue import GlueFormatter as SourceGlueFormatter

# Uppercase regexp
uppercase = re.compile("^[A-Z]$")


class GlueFormatter(SourceGlueFormatter):
    HEADERS = ["form", "lemma", "POS", "morph"]
    MORPH_PART = ["MODE", "TEMPS", "PERS.", "NOMB.", "GENRE", "CAS", "DEGRE"]

    PONCTU = re.compile(r"^\W+$")
    NUMBER = re.compile(r"\d+")
    PONFORT = [".", "...", "!", "?"]

    def __init__(self, tasks):
        self.tasks = tasks
        self.pos_tag = "POS"
        if "POS" not in self.tasks and "pos" in self.tasks:
            self.pos_tag = "pos"

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

        overwriten = self.rule_based(token)
        if overwriten:
            return overwriten

        if type(self).NUMBER.match(token):
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
            ) or "MORPH=empty"
        ]
