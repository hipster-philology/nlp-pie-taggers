from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Early Modern French",
        "freem",
        ["Simon Gabay", "Jean-Baptiste Camps", "Thibault Clérice", "Jean-Baptiste Tanguy", "Matthias Gille-Levenson",
         "Florian Cafiero"],
        "Standardizing linguistic data: method and tools for annotating(pre-orthographic) French",
        "https://github.com/e-ditiones/LEM17"
)
VERSION ="v1"
DOWNLOADS = [
        File(f"https://github.com/e-ditiones/LEM17/releases/download/{VERSION}/lemma.tar", "lemma.tar"),
        File(f"https://github.com/e-ditiones/LEM17/releases/download/{VERSION}/pos.tar", "pos.tar")
]


Models = "<{},lemma><{},POS,MODE,TEMPS,PERS,NOMB,GENRE,CAS>".format(
        get_path("freem", "lemma.tar"),
        get_path("freem", "pos.tar")
)
