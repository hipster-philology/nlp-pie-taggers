from typing import List

LASLA = ['A', 'Ap', 'App', 'Apr', 'April', 'C', 'Cn', 'D', 'Epigr', 'Febr', 'G', 'III', 'Ian', 'Id', 'Iun', 'Kal',
         'Kalend', 'L', 'LVIIII', 'LXXII', 'LXXXIIII', 'M', 'Mam', 'Mart', 'N', 'Non', 'Nou', 'Octob', 'P', 'Q',
         'Quintil', 'R', 'S', 'Ser', 'Seru', 'Sex', 'Sp', 'T', 'Ti', 'Tib', 'VII', 'XIII']


PRAENOMINA = [
    "a",
    "agr",
    "ap",
    "c",
    "cn",
    "d",
    "f",
    "k",
    "l",
    "m'",
    "m",
    "mam",
    "n",
    "oct",
    "opet",
    "p",
    "post",
    "pro",
    "q",
    "s",
    "ser",
    "sert",
    "sex",
    "st",
    "t",
    "ti",
    "v",
    "vol",
    "vop",
    "a",
    "ap",
    "c",
    "cn",
    "d",
    "f",
    "k",
    "l",
    "m",
    "m'",
    "mam",
    "n",
    "oct",
    "opet",
    "p",
    "paul",
    "post",
    "pro",
    "q",
    "ser",
    "sert",
    "sex",
    "sp",
    "st",
    "sta",
    "t",
    "ti",
    "v",
    "vol",
    "vop",
]

CALENDAR = [
    "ian",
    "febr",
    "mart",
    "apr",
    "mai",
    "iun",
    "iul",
    "aug",
    "sept",
    "oct",
    "nov",
    "dec",
] + ["kal", "non", "id", "a.d"]

MISC = ["coll", "cos", "ord", "pl.", "s.c", "suff", "trib"]

CLTK = [
    string.replace("v", "u").replace("j", "i").capitalize()+"."
    for string in MISC + CALENDAR + PRAENOMINA
]

abbrs: List[str] = sorted(list(set(CLTK + LASLA)))
