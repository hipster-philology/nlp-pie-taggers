from ...utils import Metadata, File, get_path

DESC = Metadata(
    "Ancien Francais (ENC)",
    "fro",
    ["Jean-Baptiste Camps", "Ariane Pinche", "Thibault Clérice", "Frédéric Duval", "Lucence Ing", "Naomi KANAOKA"],
    "Model trained on diverse corpora (hagiography, geste, etc.)",
    "https://github.com/chartes/deucalion-model-af"
)

VERSION = "0.4.1"

DOWNLOADS = [
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/lemma.tar",
         "lemma.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/CAS.tar",
         "CAS.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/DEGRE.tar",
         "DEGRE.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/GENRE.tar",
         "GENRE.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/MODE.tar",
         "MODE.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/NOMB.tar",
         "NOMB.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/PERS.tar",
         "PERS.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/TEMPS.tar",
         "TEMPS.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/POS.tar",
         "POS.tar"),
]

Models = "".join([
    "<{},MODE>".format(get_path("fro", "MODE.tar")),
    "<{},TEMPS>".format(get_path("fro", "TEMPS.tar")),
    "<{},PERS>".format(get_path("fro", "PERS.tar")),
    "<{},NOMB>".format(get_path("fro", "NOMB.tar")),
    "<{},GENRE>".format(get_path("fro", "GENRE.tar")),
    "<{},CAS>".format(get_path("fro", "CAS.tar")),
    "<{},DEGRE>".format(get_path("fro", "DEGRE.tar")),
    "<{},lemma>".format(get_path("fro", "lemma.tar")),
    "<{},POS>".format(get_path("fro", "POS.tar")),
])
