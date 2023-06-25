import os
from iza.nbs import NotebookAggregator


NBS_DIR = os.path.abspath('./nbs')


nbagg = NotebookAggregator(
    os.path.join(NBS_DIR, '_01_static'), module='static', 
    ignore=['_00_init.ipynb']
).aggregate()

nbagg = NotebookAggregator(os.path.join(NBS_DIR, '_02_utils'), module='utils',)
nbagg.aggregate()

nbagg = NotebookAggregator(os.path.join(NBS_DIR, '_03_types'), module='types',)
nbagg.aggregate()