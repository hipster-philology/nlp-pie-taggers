from ...utils import Metadata, File, get_path

DESC = Metadata(
    "Ancien Francais (ENC)",
    "fro",
    ["Jean-Baptiste Camps", "Ariane Pinche", "Thibault Clérice", "Frédéric Duval", "Lucence Ing", "Naomi KANAOKA"],
    "Model trained on diverse corpora (hagiography, geste, etc.)",
    "https://github.com/chartes/deucalion-model-af"
)

VERSION = "0.3.0"

DOWNLOADS = [
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/lemma-pos.tar",
         "lemma-pos.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/cas.tar",
         "cas.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/degre.tar",
         "degre.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/genre.tar",
         "genre.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/mode.tar",
         "mode.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/nomb.tar",
         "nomb.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/pers.tar",
         "pers.tar"),
    File("https://github.com/chartes/deucalion-model-af/releases/download/" + VERSION + "/temps.tar",
         "temps.tar"),
]

Models = "".join([
    "<{},MODE>".format(get_path("fro", "MODE.tar".lower())),
    "<{},TEMPS>".format(get_path("fro", "TEMPS.tar".lower())),
    "<{},PERS>".format(get_path("fro", "PERS.tar".lower())),
    "<{},NOMB>".format(get_path("fro", "NOMB.tar".lower())),
    "<{},GENRE>".format(get_path("fro", "GENRE.tar".lower())),
    "<{},CAS>".format(get_path("fro", "CAS.tar".lower())),
    "<{},DEGRE>".format(get_path("fro", "DEGRE.tar".lower())),
    "<{},lemma,POS>".format(
        get_path("fro", "lemma-pos.tar")
    )
])
