# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_imp.ipynb.

# %% auto 0
__all__ = ['TorchImp', 'TqdmImp', 'RichImp', 'ScanPyImp', 'SCPrepImp', 'is_rich_available', 'is_pytorch_available',
           'is_anndata_available']

# %% ../nbs/00_imp.ipynb 4
from ipos.imp import Imp, ImpSubSpec, ImpItem, ImpSubSpecType, is_mod_imp, is_mod, VariableDict
from dataclasses import dataclass, field

# %% ../nbs/00_imp.ipynb 6
@dataclass
class TorchImp(Imp):
    name: str = 'torch'
    lazy: bool = False
    subspecs: ImpSubSpecType = field(default_factory = lambda: [])

@dataclass
class TqdmImp(Imp):
    name: str = 'tqdm'
    subspecs: ImpSubSpecType = field(default_factory = lambda: [
        ImpSubSpec('tqdm', 'auto', [ImpItem('tqdm')])
    ])

@dataclass
class RichImp(Imp):
    name: str = 'rich'
    lazy: bool = False
    namespace: VariableDict = field(default_factory=globals, repr=False)
    subspecs: ImpSubSpecType = field(default_factory = lambda: [
        ImpSubSpec.from_str('from rich.tree import Tree'),
        ImpSubSpec.from_str('from rich.text import Text'),
        ImpSubSpec.from_str('from rich.markup import espace'),
        ImpSubSpec.from_str('from rich.filesize import decimal'),
        ImpSubSpec.from_str('from rich.filesize import Console'),
        ImpSubSpec.from_str('from rich.progress import Progress'),    
        ImpSubSpec('rich', '', [ImpItem('get_console')])
    ])

@dataclass
class ScanPyImp(Imp):
    name: str = 'scanpy'
    nick: str = 'sc'
    subspecs: ImpSubSpecType = field(default_factory = lambda: [
        ImpSubSpec('scanpy', '', [ImpItem('AnnData'), ImpItem('read_h5ad')]),
    ])

@dataclass
class SCPrepImp(Imp):
    name: str = 'scprep'    
    subspecs: ImpSubSpecType = field(default_factory = lambda: [
        ImpSubSpec('scanpy', 'io', [ImpItem('load_mtx')]),
    ])

# %% ../nbs/00_imp.ipynb 8
def is_rich_available() -> bool:
    try:
        import rich
        return True
    except ImportError:
        return False

def is_pytorch_available() -> bool: 
    try:
        import torch
        return True
    except ImportError:
        return False

def is_anndata_available() -> bool:    
    try:
        import anndata 
        return True
    except ImportError:
        return False
