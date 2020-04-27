import regex as re
from typing import List, Generator

from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer

_Dots_except_apostrophe = r".?!\"“”\"«»…\[\]\(\)„“"
_Dots_collections = r"[" + _Dots_except_apostrophe + "‘’]"
_RomanNumber = r"(?:M{1,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|C?D|D?C{1,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|M{0,4}" \
               r"(?:CM|CD|D?C{0,3})(?:XC|X?L|L?X{1,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|CD|D?C{0,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|I?V|V?I{1,3}))"


class FrMemorizingTokenizer(MemorizingTokenizer):
    APOSTROPHES = "'’ʼ"
    re_elision_apostrophe = re.compile(r"(\w+)([" + APOSTROPHES + r"])(\w+)")
    re_aujourdhui = re.compile("(aujourd)(["+APOSTROPHES+"])(hui)", flags=re.IGNORECASE)
    re_apostrophe = re.compile("(字1)")
    re_add_space_around_punct = re.compile(r"(\s*)([^\w\s])(\s*)")
    re_add_space_around_apostrophe_that_are_quotes = re.compile(
        r"("
        r"(((?<=[\W])[\'’ʼ]+(?=[\W]))|"
        r"((?<=[\w])[\'’ʼ]+(?=[\W]))|"
        r"((?<=[\W])[\'’ʼ]+(?=[\w])))|"
        r"(^[\'’ʼ]+)|"
        r"([\'’ʼ]+$))"
        # NotLetter+Apo+NotLetter or Letter+Apo+NotLetter or NotLetter+Apo+Letter + Starting or ending apostrophe
        # ?'. or manger'_ or _'Bonjour
    )
    re_add_space_after_apostrophe = re.compile(r"(\s*)([\'’ʼ])(\s*)")
    re_remove_ending_apostrophe = re.compile(r"(?<=\w)([\'’ʼ])")
    _sentence_boundaries = re.compile(
        r"([" + _Dots_except_apostrophe + r"]+\s*)+"
    )
    roman_number_dot = re.compile(r"\.(" + _RomanNumber + r")\.")
    # Need to deal with (Case insensitive)
    # - Aujourd'hui
    # - ['-ce', '-ci', '-elle', '-elles', '-en', '-eux', '-il', '-ils', '-je', '-la', '-le', '-les', '-leur', '-leurs',
    #       '-lui', '-là', '-m', '-me', '-moi', '-même', '-mêmes', '-nous', '-on', '-t', '-te', '-toi', '-tu', '-un',
    #       '-une', '-unes', '-uns', '-vous', '-y']
    # - peut-être, peut-estre, sur-tout, long-temps, par-tout, vis-à-vis
    # a-t-il -> a / -t-il

    _data_re_keep_clitics_pronouns = [
        '-ce', '-ci', '-elle', '-elles', '-en', '-eux', '-il', '-ils', '-je', '-la', '-le',
        '-les', '-leur', '-leurs',
        '-lui', '-là', '-m', '-me', '-moi', '-même', '-mêmes', '-nous', '-on', '-t',
        '-te', '-toi', '-tu', '-un',
        '-une', '-unes', '-uns', '-vous', '-y',
        r'-m字\d', r'-t字\d'  # 字 replaces all kinds of apostrophe
    ]

    re_keep_clitics = re.compile(
        r"(-)("+r"|".join(
            [tok.replace("-", "") for tok in sorted(_data_re_keep_clitics_pronouns, key=len, reverse=True)]
        )+r")(\b|$)",
        flags=re.IGNORECASE
    )

    # Not used currently
    _data_re_keep_together = "peut-être, peut-estre, sur-tout, long-temps, par-tout, vis-à-vis".split(", ")
    re_keep_together = re.compile(
        r"("+"|".join([
            token
            for token in _data_re_keep_together
        ])+r")(?:\b|$)",
        flags=re.IGNORECASE
    )

    # Abbreviations separated by `; ` (SEMICOLON+SPACE)
    # You can use regexp inside this list, such as [Cc]f. but I would rather recommend to add both `cf.; Cf;`
    #   for readability.
    _data_re_abbr = sorted(list(set(
        "Acad.; Adj.; Agricol.; Agricul.; Apocal.; anc.; Bot.; Botan.; Botaniq.; ca.; cap.; capi.; cf.; Cf.; " 
        "Cha.; Chap.; Col.; Dic.; Diction.; Dictionn.; Eccl.; Écon.; Élem.; Fig.; Fr.; Geog.; Gram.; " 
        "Gramm.; Hist.; Ibid.; Ibid.; Inst.; Jard.; Jurisprud.; Latit.; Li.; Lib.; Libr.; Lig.; Lit.; " 
        "Littérat.; Liv.; Long.; Mar.; Mat.; Mathém.; Mech.; Med.; Med.; Mem.; Menuis.; Milit.; Mod.; " 
        "Mor.; Mr.; Monsr.; nat.; natur.; N.b.; Orat.; Ornith.; Ornythol.; Ornitholog.; Part.; Pag.; " 
        "Pharm.; Phil.; Philos.; Pl.; Pl.; Politiq.; P.S.; Phys.; Physiq.; Sr.; St.; Subst.; s.f.; " 
        "S.M.; s.m.; Tab.; Théât.; Trév.; Tom.; Vol.; V. n.; V. a.; V. act.; Zoo.; " 
        "Zoolog.".split("; ")
    )), key=len, reverse=True)
    re_abbr = re.compile(
        r"\b("+"|".join([
            token.replace(" ", r"\s+").replace(".", r"\.")
            for token in _data_re_abbr
            if token
        ])+r")"
    )

    def __init__(self):
        super(FrMemorizingTokenizer, self).__init__()
        self.tokens = []

    @staticmethod
    def _sentence_tokenizer_merge_matches(match):
        """ Best way we found to deal with repeating groups"""
        start, end = match.span()
        return match.string[start:end] + "<SPLIT>"

    def _real_sentence_tokenizer(self, string: str) -> List[str]:
        string = self._sentence_boundaries.sub(self._sentence_tokenizer_merge_matches, string)

        for index_apo, apo in enumerate(self.APOSTROPHES):
            string = string.replace("字"+str(index_apo), apo)

        string = string.replace("界t 界", "-t-")
        string = string.replace("界", "-")  # Any dash separating pronouns
        #string = string.replace("分", "-")  # Agglutinated words such as peut-être
        string = string.replace("語", ".")  # Dots from abbreviations
        return string.split("<SPLIT>")

    def _real_word_tokenizer(self, text: str, lower: bool = False) -> List[str]:
        if lower:
            text = text.lower()
        text = text.split()
        return text

    def sentence_tokenizer(self, text: str, lower: bool = False) -> Generator[List[str], None, None]:
        sentences = list()
        data = self.normalizer(text)
        for sent in self._real_sentence_tokenizer(data):
            sent = sent.strip()
            if sent:
                sentences.append(self.word_tokenizer(sent))
        yield from sentences

    def replace_apostrophe(self, regex_match) -> str:
        return regex_match.group(1) + "字" + str(self.APOSTROPHES.index(regex_match.group(2))) \
               + " " + regex_match.group(3)

    def replace_keep_together(self, regex_match) -> str:
        return regex_match.group(0).replace("-", "分")

    def replace_aujourdhui(self, regex_match) -> str:
        return regex_match.group(1) + "字" + str(self.APOSTROPHES.index(regex_match.group(2))) + regex_match.group(3)

    def replace_abbr_dot(self, regex_match) -> str:
        return regex_match.group(1).replace(".", "語")

    def normalizer(self, data: str) -> str:
        data = self.re_add_space_around_punct.sub(
                    r" \g<2> ",
                    self.re_abbr.sub(
                        self.replace_abbr_dot,
                        # peut-etre, etc.
                        #self.re_keep_together.sub(
                        #    self.replace_keep_together,
                            self.re_keep_clitics.sub(
                                r" 界\2",
                                self.re_elision_apostrophe.sub(
                                    self.replace_apostrophe,
                                    self.re_aujourdhui.sub(
                                        self.replace_aujourdhui,
                                        data
                                    )
                                )
                            )
                        #)
                    )
                )
        return data

    def replacer(self, inp: str):
        return self.re_remove_ending_apostrophe.sub("'", inp)\
            .replace("-t-", "-")  # Temp feature until retrain has been done
