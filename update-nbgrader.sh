#!/bin/bash

# Updates two lines of nbgrader 0.6.1 to make them compatible
# with the lates version of cds.
# The script is only guaranteed to work with nbgrader 0.6.1.  
#
# The script has the path of nbgrader hard coded. If tha path changes, the script has to be updated accordingly.

sed -i '67 s/])$/&.tag(config=True)/' /opt/conda/lib/python3.8/site-packages/nbgrader/converters/generate_assignment.py
sed -i '59 s/])$/&.tag(config=True)/' /opt/conda/lib/python3.8/site-packages/nbgrader/converters/autograde.py
