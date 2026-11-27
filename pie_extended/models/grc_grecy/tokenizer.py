import regex as re
import unicodedata

from pie_extended.models.grc.tokenizer import GrcMemorizingTokenizer

# GreCy only handles elisions if they are written with the modifier letter apostrophe (U+02BC)
MODIFIER_APOSTROPHE = "ʼ"
# Every way to write an apostrophe/elision mark: ASCII, right quote, koronis (U+1FBD), psili (U+1FBF), modifier letter
APOSTROPHES = "'’᾽᾿ʼ"
_APOSTROPHES = re.compile("[{}]".format(APOSTROPHES))


class GreCyMemorizingTokenizer(GrcMemorizingTokenizer):
    # Unlike the Pie Greek tokenizer, apostrophes are not split off: in the UD treebanks GreCy is trained on,
    # an elision is part of its word (δι᾽ αὐτοῦ -> `δι᾽`, `αὐτοῦ`). The price: a quote written with `'` stays glued.
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s{}])(\s*)".format(APOSTROPHES))

    def replacer(self, inp: str):
        for excluder in self.normalizers:
            if not excluder.can_be_replaced and excluder.exclude_regexp.match(inp):
                return inp
        # spaCy models are trained on composed characters; the original is kept in the `treated` column
        return _APOSTROPHES.sub(MODIFIER_APOSTROPHE, unicodedata.normalize("NFC", inp))
