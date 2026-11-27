Code specific to models
=======================

Armenian
--------

The three Armenian models (``hy_hye``, ``hy_hyw``, ``hy_xcl``) share one tokenizer.

.. automodule:: pie_extended.models.hy_hye.tokenizer
   :members:

Classical Armenian has one more step: the segmentation of its clitics, learned from the treebank.

.. automodule:: pie_extended.models.hy_xcl.segmenter
   :members:
