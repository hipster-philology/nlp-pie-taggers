from pie_extended.models.grc_grecy import imports as grecy
from pie_extended.models.grc_grecy.imports import get_iterator_and_processor  # noqa: F401 (same tokenization)

from . import SpacyModel, Soter


def addons(name: str = None) -> bool:
    """ What `pie-extended install-addons grc_soter` runs: installs the spaCy pipeline, and fetches Sôtêr (that is then
    in the cache of Hugging Face: it is also downloaded at first use, if you do not run this) """
    if not grecy.addons(name or SpacyModel):
        return False
    from huggingface_hub import snapshot_download
    repo = Soter.split(":", 1)[1].split("#")[0]
    print("Fetching " + repo)
    snapshot_download(repo, allow_patterns=["*.json", "*.safetensors", "tables/*"])
    return True
