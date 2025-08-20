"""Module containing a preprocessor for creating `selfTest` cells from
autograder cells."""

import nbformat as nbf
import copy

from nbgrader.preprocessors import NbGraderPreprocessor

class AddSelftestsPreprocessor(NbGraderPreprocessor):
    """Preprocessor for creating `selfTest` cells from autograder cells.
    The code of the nbgrader autograde cells are wrapped in a try/except
    block to catch and print any assertion error. If all assertions pass, the 
    string 'Correct!' is printed. Otherwise the string 'Incorrect!' is printed,
    followed by the assert message.
    
    The metadata in the selfTest cells are adjusted in the following way.
    * A ``selfTest`` entry is added and set to ``True''.
    
    The ``nbgrader`` entry in the metadata is adjusted in the following way:
    * The string '_test' is appended to the ``grade_id`` entry.
    """

    def make_selftest(self, source):
        """Takes string of Python code, wraps the code in try/except blocks to catch
        assertion errors. Returns the wrapped version of the code. Removes the delimiters
        for hidden tests.

        Parameters
        ----------
        source : str
            The code to be wrapped.

        Returns
        -------
        str
            The wrapped code.

        Examples
        --------

        >>> s1 = "assert 1 == 1, 'One should be one'"
        >>> s2 = AddSelftestPreprocessor.make_selftest(s1)
        >>> print(s2)
            def test():
                    try:
                        assert 1 == 1, 'One should be one'
                        print('Correct!')
                    except Exception as e:
                        print('Incorrect!')
                        print(e)
            test()
            del test
        """
        test_delimiters = ['BEGIN HIDDEN TESTS', 'END HIDDEN TESTS', 'nbgrader cell']
        new_source = 'def test():\n'
        new_source += '    try:\n'
        for line in source.splitlines():
            if any(delimiter in line for delimiter in test_delimiters):
                continue
            new_source += '        ' + line +'\n'
        new_source += "        print('Correct!')\n"
        new_source += "    except AssertionError as e:\n"
        new_source += "        print('Incorrect!')\n"
        new_source += "        print(e)\n"
        new_source += 'test()\n'
        new_source += 'del test'
        return new_source

    def preprocess(self, nb, resources):
        """Adds a `selfTest` cell for every autograde cell encountered.

        The function loops through each cell, searching in the metadata of the
        cell for an existing and True ``grade`` entry. Such cells are copied and
        their source code is wrapped in a try/except block to catch and print
        any assertion error. Then that cell is run the simple string 'Correct!'
        is printed if all assertions pass. If an assertion fails, the string
        'Incorrect!' will be printed, followed by the assertion message.

        The metadata in the selfTest cells are adjusted in the following way.
        * A ``selfTest`` entry is added and set to ``True''.
        * The ``tag`` ``'selfTest'`` is added.
        The ``nbgrader`` entry in the metadata is adjusted in the following way:

        * The string '_test' is appended to the ``grade_id`` entry.
        * The ``grade`` entry is set to ``False``.

        Parameters
        ----------
        nb : nbformat.NotebookNode
            The source notebook

        Returns
        -------
        nbformat.NotebookNode
            The notebook with the added selfTest cells.

        Examples
        --------

        from pprint import pprint
        >>> nb = nbformat.v4.new_notebook()
        >>> s1 = "assert 1==0, 'one is not zero'"
        >>> cell = nbformat.v4.new_code_cell(s1)
        >>> cell['metadata']['nbgrader']={'grade_id':'Q1', 'grade': True}
        >>> nb['cells']=[cell]
        >>> nb2 = AddSelftestPreprocessor.preprocess(nb)
        >>> pprint(nb2['cells'])
        [{'cell_type': 'code',
        'execution_count': None,
        'id': 'b9cf473a',
        'metadata': {'hideCell': True,
                    'nbgrader': {'grade': False, 'grade_id': 'Q1_self-test'},
                    'selfTest': True},
        'outputs': [],
        'source': 'try:\n'
                    "    assert 1==0, 'one is not zero'\n"
                    "    print('Correct!')\n"
                    'except AssertionError as e:\n'
                    '    print("Incorrect!")\n'
                    '    print(e)'},
        {'cell_type': 'code',
        'execution_count': None,
        'id': 'e20c61e3',
        'metadata': {'nbgrader': {'grade': True, 'grade_id': 'Q1'}},
        'outputs': [],
        'source': "assert 1==0, 'one is not zero'"}]
        """
        # copy cells and add selfTest cells
        new_cells = list()
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                if cell['metadata'].get('nbgrader'):
                    if cell['metadata']['nbgrader'].get('grade'):
                        # This is a cell we want to create a self-test
                        cell_new = nbf.v4.new_code_cell()
                        cell_new['source'] = self.make_selftest(cell['source'])
                        cell_new['metadata'] = copy.deepcopy(cell['metadata'])
                        
                        # adjust metadata
                        cell_new['metadata'].setdefault('tags', [])\
                            .append('selfTest')
                        cell_new['metadata']['selfTest'] = True
                        cell_new['metadata']['hideCell'] = True
                        cell_new['metadata']['nbgrader']['grade'] = False
                        cell_new['metadata']['nbgrader']['grade_id'] =\
                            cell['metadata']['nbgrader'].get('grade_id', '')\
                                +'_self-test'

                        # Adjust the cell code to catch AssertionErrors
                        #  and display feedback.
                        new_cells.append(cell_new)
            new_cells.append(cell)
        nb['cells'] = new_cells
        return nb, resources
