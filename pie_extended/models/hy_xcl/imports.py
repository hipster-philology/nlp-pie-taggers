import os
import tempfile

from pie_extended.models.hy_hye.imports import get_iterator_and_processor as _get_iterator_and_processor
from pie_extended.models.hy_xcl import segmenter as clitics

# Treebank the Pie model was trained on. CC BY-NC-SA 4.0: it is downloaded for the user, never redistributed.
TREEBANK = "https://raw.githubusercontent.com/UniversalDependencies/UD_Classical_Armenian-CAVaL/master/xcl_caval-ud-{}.conllu"


def get_iterator_and_processor(max_tokens=256):
    """ Same tokenization as the other Armenian models, plus the segmentation of the clitics (as in the treebank)
    if it was learned (`pie-extended install-addons hy_xcl`) """
    return _get_iterator_and_processor(max_tokens=max_tokens, segmenter=clitics.load_default())


def addons() -> bool:
    """ Learns where the Universal Dependencies treebank of Classical Armenian cuts the clitics (`զմեղս` -> `զ`, `մեղս`)

    The model expects pre-tokenized words like the ones of this treebank. The treebank is downloaded and the
    segmenter is trained (a few seconds); only what it learned is kept, in the downloads of the model.
    """
    from pie_extended.cli.utils import _download

    with tempfile.TemporaryDirectory() as directory:
        sentences = {}
        for split in ("train", "dev", "test"):
            path = os.path.join(directory, split + ".conllu")
            _download(TREEBANK.format(split), path)
            sentences[split] = list(clitics.read_conllu(path))

        # Honest score: what the segmenter does on sentences it has not seen
        segmenter = clitics.train(clitics.training_examples(sentences["train"]))
        scores = clitics.evaluate(segmenter, sentences["test"])
        print("Test set of the treebank: cut points F1 = {:.1f}% (P = {:.1f}%, R = {:.1f}%), "
              "sentences with exactly the words of the treebank: {:.1f}%".format(
                  100 * scores["f1"], 100 * scores["precision"], 100 * scores["recall"],
                  100 * scores["sentences_exact"]))

        # The one that is kept learns from all that is not the test set
        segmenter = clitics.train(clitics.training_examples(sentences["train"] + sentences["dev"]))
        segmenter.save(clitics.default_path())
    print("Saved in " + clitics.default_path())
    return True
