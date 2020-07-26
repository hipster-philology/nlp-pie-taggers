from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Early Modern French",
        "freem",
        ["Simon Gabay", "Jean-Baptiste Camps", "Thibault Clérice", "Jean-Baptiste Tanguy", "Matthias Gille-Levenson",
         "Florian Cafiero"],
        "Standardizing linguistic data: method and tools for annotating(pre-orthographic) French",
        "https://github.com/e-ditiones/LEM17"
)

DOWNLOADS = [
        File("https://github.com/e-ditiones/LEM17/raw/7ec86d61c9d13cc8d0e56d6dd37971f0f220ad70/"
             "Models/Train_2/models/lemma.tar", "lemma.tar"),
        File("https://github.com/e-ditiones/LEM17/raw/7ec86d61c9d13cc8d0e56d6dd37971f0f220ad70/"
             "Models/Train_2/models/pos.tar", "pos.tar")
]


Models = "<{},lemma><{},POS>".format(
        get_path("freem", "lemma.tar"),
        get_path("freem", "pos.tar")
)
