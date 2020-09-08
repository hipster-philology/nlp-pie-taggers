import pie_extended.pipeline.tokenizers.utils.chars as chars


RomanNumbers = r"(?:M{1,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|C?D|D?C{1,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|M{0,4}" \
               r"(?:CM|CD|D?C{0,3})(?:XC|X?L|L?X{1,3})" \
               r"(?:IX|IV|V?I{0,3})|M{0,4}(?:CM|CD|D?C{0,3})" \
               r"(?:XC|XL|L?X{0,3})(?:IX|I?V|V?I{1,3}))"


DOTS_EXCEPT_APOSTROPHES = r"[" + chars.DOTS_EXCEPT_APOSTROPHES + "‘’]"
ENDING_APOSTROPHE = r"(?<=\w)([\'’ʼ])"

NON_WORD_NON_SPACE = r"(\s*)([^\w\s])(\s*)"
