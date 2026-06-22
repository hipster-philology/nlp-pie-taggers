from ...utils import Metadata, File, get_path

DESC = Metadata(
    "Moyen Français (ENC)",
    "frm",
    ["Dugaz, Lucien", "Ing, Lucence", "Vidal-Gorène, Chahan", "Duval, Frédéric"],
    "Model trained on diverse corpora (1300–1529) for lemmatization, POS-tagging, and morphological analysis of Middle French",
    "https://zenodo.org/records/20522515"
)

VERSION = "20522515"

BASE_URL = "https://zenodo.org/records/" + VERSION + "/files/"

DOWNLOADS = [
    File(BASE_URL + "mf-lemma-best-2026_03_19-10_32_49.tar?download=1",
         "lemma.tar"),
    File(BASE_URL + "mf-CAS-best-2026_03_18-19_32_25.tar?download=1",
         "CAS.tar"),
    File(BASE_URL + "mf-DEGRE-best-2026_03_19-02_42_52.tar?download=1",
         "DEGRE.tar"),
    File(BASE_URL + "mf-GENRE-best-2026_03_19-08_42_57.tar?download=1",
         "GENRE.tar"),
    File(BASE_URL + "mf-MODE-best-2026_03_19-11_08_54.tar?download=1",
         "MODE.tar"),
    File(BASE_URL + "mf-NOMB-best-2026_03_19-16_26_12.tar?download=1",
         "NOMB.tar"),
    File(BASE_URL + "mf-PERS-best-2026_03_19-19_43_38.tar?download=1",
         "PERS.tar"),
    File(BASE_URL + "mf-TEMPS-best-2026_03_19-20_23_24.tar?download=1",
         "TEMPS.tar"),
    File(BASE_URL + "mf-POS-best-2026_03_19-19_58_03.tar?download=1",
         "POS.tar"),
]

Models = "".join([
    "<{},MODE>".format(get_path("frm", "MODE.tar")),
    "<{},TEMPS>".format(get_path("frm", "TEMPS.tar")),
    "<{},PERS>".format(get_path("frm", "PERS.tar")),
    "<{},NOMB>".format(get_path("frm", "NOMB.tar")),
    "<{},GENRE>".format(get_path("frm", "GENRE.tar")),
    "<{},CAS>".format(get_path("frm", "CAS.tar")),
    "<{},DEGRE>".format(get_path("frm", "DEGRE.tar")),
    "<{},lemma>".format(get_path("frm", "lemma.tar")),
    "<{},POS>".format(get_path("frm", "POS.tar")),
])