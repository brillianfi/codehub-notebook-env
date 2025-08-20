"""Module containing a preprocessor to remove notebook cells with
the tag `'self_test'`."""
from nbconvert.preprocessors import TagRemovePreprocessor
from nbgrader.preprocessors import NbGraderPreprocessor
from traitlets import Set

class RemoveSelftestsPreprocessor(NbGraderPreprocessor,TagRemovePreprocessor):
    """Removes cells with the tag `'selfTest'`."""
    remove_cell_tags = Set(['selfTest'])