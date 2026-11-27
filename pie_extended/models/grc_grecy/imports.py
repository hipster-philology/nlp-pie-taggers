import subprocess
import sys

from .tokenizer import GreCyMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor

GRECY_VERSION = "v3.8.2"
WHEEL = "https://github.com/jmyerston/greCy/releases/download/{v}/{name}-{v_}-py3-none-any.whl"


def get_iterator_and_processor(max_tokens=256):
    tokenizer = GreCyMemorizingTokenizer()
    processor = MemoryzingProcessor(
        tokenizer_memory=tokenizer,
        head_processor=ProcessorPrototype()
    )

    iterator = DataIterator(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        exclude_patterns=[
            excl.exclude_regexp
            for excl in tokenizer.normalizers
            if excl.exclude_regexp
        ]
    )
    return iterator, processor


def addons(name: str = "grc_proiel_sm") -> bool:
    """ Installs the spaCy pipeline (a wheel published on GreCy's releases) in the current environment """
    url = WHEEL.format(v=GRECY_VERSION, v_=GRECY_VERSION.lstrip("v"), name=name)
    command = [sys.executable, "-m", "pip", "install", url]
    print("Running: " + " ".join(command))
    return subprocess.call(command) == 0
