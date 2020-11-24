from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Middle Dutch",
        "dum",
        ["Mike Kestemont"],
        "Middle Dutch Model",
        "https://github.com/hipster-philology/middle-dutch-model"
)

VERSION = "0.0.1"
DOWNLOADS = [
    File(f"https://github.com/hipster-philology/middle-dutch-model/releases/download/{VERSION}/lemma.tar", "lemma.tar"),
    File(f"https://github.com/hipster-philology/middle-dutch-model/releases/download/{VERSION}/pos.tar", "pos.tar")
]


Models = "<{},lemma><{},pos>".format(
        get_path("dum", "lemma.tar"),
        get_path("dum", "pos.tar")
)
