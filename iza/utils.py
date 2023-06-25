# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_utils.ipynb.

# %% auto 0
__all__ = ['isiter', 'allinstance', 'allsametype', 'isin', 'arein', 'str_just_alpha', 'str_just_numeric', 'strip_punc',
           'filter_kwargs_for_func', 'filter_kwargs_for_class', 'wrangle_kwargs_for_func', 'wrangle_kwargs_for_class',
           'get_user', 'collapse_user', 'check_ext', 'drop_ext', 'is_tar', 'is_gz', 'is_targz', 'is_tarball',
           'filter_for_gz_files', 'get_gz_files_in_dir', 'decompress_tarball', 'decompress_gunzip', 'undo_gz',
           'make_missing_dirs', 'dir_dirs', 'decompress_directory_of_gunzipped_files',
           'decompress_tarball_of_gunzipped_files', 'stream_file', 'download_and_decompress_tarball_of_gunzipped_files',
           'make_temp_file', 'Slice', 'Directory', 'is_matrix', 'undo_npmatrix', 'is_series', 'is_series_like', 'is_np',
           'is_device', 'is_cpu', 'is_mps', 'is_tensor', 'is_torch', 'config_exp_logger', 'exp_log_filename',
           'exp_param_filename', 'list_exps', 'gen_exp_name', 'load_exp_params', 'save_exp_params', 'setup_exp',
           'is_config_subset', 'find_exps']

# %% ../nbs/02_utils.ipynb 5
import inspect, string
from dataclasses import dataclass, field

import numpy as np, pandas as pd

from typing import List, Any, Optional, Callable, Union, Tuple, Iterable, Set, TypeAlias, Type

# %% ../nbs/02_utils.ipynb 7
def isiter(val: Any) -> bool:    
    return isinstance(val, Iterable)

def allinstance(vals:Any, dtype:Union[Type, TypeAlias]=Any) -> bool:
    return isiter(vals) and all(isinstance(i, dtype) for i in vals)

def allsametype(vals:Any) -> bool:
    if not isiter(vals) or len(vals) == 0: return True
    dtype = type(vals[0])
    return isiter(vals) and all(isinstance(i, dtype) for i in vals)

def isin(val:Any, vals:Iterable) -> bool:
    return val in vals

def arein(vals:Iterable, refs:Iterable) -> bool:                                             
    return isiter(vals) and isiter(refs) and all(isin(v, refs) for v in vals)

# %% ../nbs/02_utils.ipynb 8
def str_just_alpha(s:str) -> str:
    '''Filters a string for just alpha values'''
    return ''.join(list(filter(str.isalpha, s)))

def str_just_numeric(s:str) -> str:
    '''Filters a string for just numeric values'''
    return ''.join(list(filter(str.isnumeric, s)))

def strip_punc(s:str) -> str:
    return s.translate(str.maketrans('', '', string.punctuation))

# %% ../nbs/02_utils.ipynb 10
def filter_kwargs_for_func(fn: Callable, **kwargs:Optional[dict]):
    params = inspect.signature(fn).parameters
    return {k:v for k,v in kwargs.items() if k in params}

def filter_kwargs_for_class(cls: Callable, **kwargs:Optional[dict]):
    params = inspect.signature(cls.__init__).parameters
    return {k:v for k,v in kwargs.items() if k in params}

def wrangle_kwargs_for_func(
    fn: Callable, 
    defaults: Optional[dict]=None,
    **kwargs:Optional[dict]
) -> dict:
    # copy defaults
    params = (defaults or {}).copy()
    # update with kwargs of our function
    params.update(kwargs or {})
    # filter for only the params that other function accepts
    params = filter_kwargs_for_func(fn, **params)
    return params

def wrangle_kwargs_for_class(
    cls: Callable, 
    defaults: Optional[dict]=None,
    **kwargs:Optional[dict]
) -> dict:
    # copy defaults
    params = (defaults or {}).copy()
    # update with kwargs of our class
    params.update(kwargs or {})
    # filter for only the params that other class accepts
    params = filter_kwargs_for_class(cls, **params)
    return params

# %% ../nbs/02_utils.ipynb 12
import os, sys, pwd, atexit, tempfile, inspect
import requests, tarfile, gzip, shutil

from tqdm.auto import tqdm

from typing import Optional, List, Union, Iterable, Tuple

# %% ../nbs/02_utils.ipynb 13
from iza.static import (
    EXT_GZ, EXT_TAR, EXT_TAR_GZ,
)

# %% ../nbs/02_utils.ipynb 15
def get_user() -> str:
    user = pwd.getpwuid(os.getuid())[0]
    return user

def collapse_user(path: str) -> str:
    _, rest = path.split(get_user())    
    return '~' + rest

# %% ../nbs/02_utils.ipynb 17
def check_ext(filename:str, extension:str) -> bool:
    has_extension = extension in filename 
    splits = filename.split(extension)
    is_end_of_str = len(splits) >= 2 and splits[-1] == ''
    is_end_of_str = filename.endswith(extension)
    return has_extension and is_end_of_str

def drop_ext(filename:str, extension:Optional[str]=None) -> str:
    file = os.path.basename(filename)
    if extension is None:
        file, *_ = file.split('.')
    else:
        file = filename.replace(extension, '')
    return os.path.join(os.path.dirname(filename), file)

# %% ../nbs/02_utils.ipynb 18
def is_tar(filename:str) -> bool:
    return check_ext(filename, EXT_TAR)

def is_gz(filename:str) -> bool:
    return check_ext(filename, EXT_GZ)

def is_targz(filename:str) -> bool:
    return check_ext(filename, EXT_TAR_GZ)

def is_tarball(filename:str) -> bool:
    return is_tar(filename) or is_targz(filename)


# %% ../nbs/02_utils.ipynb 19
def filter_for_gz_files(files:List[str]) -> List[str]:
    return list(filter(lambda f: is_gz(f), files))

def get_gz_files_in_dir(dirname:str) -> List[str]:
    all_files = []

    for (root, dirs, files) in os.walk(dirname):   
        fullpaths = [os.path.join(root, file) for file in files]
        all_files.extend(fullpaths)
    
    gz_files = filter_for_gz_files(all_files)
    return gz_files

# %% ../nbs/02_utils.ipynb 21
def decompress_tarball(filename:str) -> Tuple[str, Optional[EOFError]]:
    '''
    Returns
    -------
        dirname : str
            The name of the archive e.g. `~/Downloads/fluentbio.tar.gz` would
            yield `~/Downloads/fluentbio`


    Notes
    -----
    FluentBio has a weird gzip so it complains when it is 
        actually fine
    '''
    error = None
    decompress_dir = os.path.dirname(filename)
    dirname = drop_ext(filename, EXT_TAR_GZ)
    try:
        with tarfile.open(filename) as tarball:
            tarball.extractall(decompress_dir)
            tarball.close()

    except EOFError as error:
        pass

    return dirname, error


def decompress_gunzip(filename:str, remove:bool=False) -> Tuple[str, Optional[EOFError]]:
    '''
    Returns
    -------
        file : str
            The name of the decompressed file e.g. `~/Downloads/fluentbio.tsv.gz` would
            yield `~/Downloads/fluentbio.tsv`

    Notes
    -----
    FluentBio has a weird gzip so it complains when it is 
        actually fine
    '''
    error = None
    decompressed_file = drop_ext(filename, EXT_GZ)
    try:             
        with gzip.open(filename, 'rb') as gunzipped:
            with open(decompressed_file, 'wb') as unzipped:
                shutil.copyfileobj(gunzipped, unzipped)     
                   
    except EOFError as error:
        pass

    if os.path.isfile(decompressed_file) and remove:
        os.remove(filename)

    return decompressed_file, error

def undo_gz(filename: str) -> str:
    if is_gz(filename):
        filename, _ = decompress_gunzip(filename, remove=True)
    elif is_tarball(filename):
        filename, _ = decompress_tarball(filename)
    return filename

# %% ../nbs/02_utils.ipynb 23
def make_missing_dirs(dirs:List[str]):
    if isinstance(dirs, str):
        dirs = [dirs]
        
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            
def dir_dirs(dirname:str) -> List[str]:
    entries = os.listdir(dirname)
    is_subdir = lambda e : os.path.isdir(os.path.join(dirname, e))
    return list(filter(is_subdir, entries))

# %% ../nbs/02_utils.ipynb 24
def decompress_directory_of_gunzipped_files(
    dirname:str, desc:Optional[str]=None, remove:Optional[bool]=False
) -> None:
    if desc is None:
        desc = dirname.split('/')[-1]

    gz_files = get_gz_files_in_dir(dirname)
    for filename in tqdm(gz_files, desc=desc):
        decomp_filename, error = decompress_gunzip(filename, remove)   


def decompress_tarball_of_gunzipped_files(
    filename:str, desc:Optional[str]=None, remove:Optional[bool]=False
) -> None:
    # NOTE: initial decompress of .tar.gz
    dirname, error = decompress_tarball(filename)

    if desc is None:
        desc = dirname.split('/')[-1]

    # NOTE: decompress all internal .gz files
    decompress_directory_of_gunzipped_files(dirname, desc, remove)

# %% ../nbs/02_utils.ipynb 26
def stream_file(uri:str, filename:Optional[str]=None, desc:Optional[str]=None) -> None:
    '''
    Parameters
    ----------
    uri : str
        The URI to download

    filename : str, optional
        The fullpath name of the file to download. Defaults to 
        `~/Downloads/os.path.basename(uri)`.

    desc : str, optional
        The description of the `tqdm` progress bar. Defaults to 
        `os.path.basename(uri)`.
    '''
    if filename is None:
        download_dir = os.path.expanduser(f'~/Downloads')        
        filename = os.path.join(download_dir, os.path.basename(uri))

    basename = os.path.basename(filename)
    if desc is None:
        desc = basename

    response = requests.get(uri, stream=True)
    total = int(response.headers.get('content-length', 0))
    
    with tqdm.wrapattr(
        open(filename, 'wb'), 'write', 
        miniters=1, desc=desc, total=total
    ) as fout:
        for chunk in response.iter_content(chunk_size=4096):
            fout.write(chunk)

# %% ../nbs/02_utils.ipynb 28
def download_and_decompress_tarball_of_gunzipped_files(
    uri:str, download_dir:str=None, desc:Optional[str]=None, remove:Optional[bool]=False
):
    filename = os.path.basename(uri)
    fullpath = os.path.join(download_dir, filename)

    if desc is None:
        description = f'Downloading {filename}'


    # NOTE: Amazon --> filtered_matrix.tar.gz
    stream_file(uri, description)

    if desc is None:
        description = f'Decompressing {filename}'
    # NOTE: filtered_matrix.tar.gz --> filtered_matrix/**/file.tsv
    decompress_tarball_of_gunzipped_files(fullpath, desc, remove)


# %% ../nbs/02_utils.ipynb 30
def make_temp_file(**kwargs: Any) -> tempfile.NamedTemporaryFile:
    temp = tempfile.NamedTemporaryFile(**kwargs)
    @atexit.register
    def delete_temp() -> None:
        temp.close()
    return temp

# %% ../nbs/02_utils.ipynb 32
from dataclasses import dataclass, field
import numpy as np, pandas as pd

from typing import List, Union, Tuple

# %% ../nbs/02_utils.ipynb 35
@dataclass
class Slice:
    """A class for representing a slice and providing conversion to other formats."""
    slc: slice = field(default_factory=slice)

    @property
    def start(self):
        try:
            return self._start
        except AttributeError:
            self._start = self.slc.start
        return self._start
    
    @start.setter
    def start(self, value):
        """Sets the start index."""
        if value < 0:
            raise ValueError("Slice indices must be non-negative.")
        self._start = value

    @property
    def stop(self):
        try:
            return self._stop
        except AttributeError:
            self._stop = self.slc.stop
        return self._stop
    
    @stop.setter
    def stop(self, value):
        """Sets the stop index."""
        if value < 0:
            raise ValueError("Slice indices must be non-negative.")
        self._stop = value
    
    @property
    def step(self):
        """Gets the step index."""
        try:
            return self._step
        except AttributeError:
            self._step = self.slc.step
        return self._step
    
    @step.setter
    def step(self, value):
        """Sets the step index."""
        if value < 0:
            raise ValueError("Slice step must be non-negative.")
        self._step = value
    
    def __post_init__(self):
        if self.start is None:
            self.start = 0

        if self.stop is None:
            self.stop = min(0, self.start, max(1, self.start))

        if self.step is None:
            self.step = 1

    def totuple(self) -> Tuple[Union[int, float, None], Union[int, float, None], Union[int, float, None]]:
        """Converts the slice to a tuple."""
        return (self.start, self.stop, self.step)
    
    def toslice(self) -> slice:
        """Converts the updated slice."""
        return slice(self.start, self.stop, self.step)
    
    def tolist(self) -> List[Union[int, float]]:
        """Converts the slice to a list."""
        return list(range(self.start, self.stop, self.step))
    
    def todict(self) -> List[Union[int, float]]:
        """Converts the slice to a dict."""
        return dict(zip('start stop step'.split(), self.totuple()))
        

    def astype(self, dtype:str):
        """Converts the slice to a specified format."""
        if dtype in {'list', list}:
            return self.tolist()
        elif dtype in {'numpy', np.ndarray}:
            return np.array(self.tolist())
        elif dtype in {'pandas', pd.Series}:
            return pd.Series(self.tolist())
        elif dtype in {'tuple', tuple}:
            return self.totuple()
        elif dtype in {'dict', dict}:
            return self.todict()
        elif dtype in {'slice', slice}:
            return self.toslice()
        return self

# %% ../nbs/02_utils.ipynb 37
import os
from pathlib import Path
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, List, ClassVar

# %% ../nbs/02_utils.ipynb 40
@dataclass
class Directory:
    dirname: str

    _: KW_ONLY
    _SPACE : ClassVar[str] = '    '
    _BRANCH: ClassVar[str] = '│   '    
    _TEE   : ClassVar[str] = '├── '
    _LAST  : ClassVar[str] = '└── '

        
    def make_tree(self, dirname:Path, prefix:str=''):
        '''
        A recursive generator, given a directory Path object
        will yield a visual tree structure line by line
        with each line prefixed by the same characters
        Notes
        -----
        Adapted from https://stackoverflow.com/a/59109706/5623899
        '''

        contents = list(dirname.iterdir())
        # NOTE: contents each get pointers that are ├── with a final └── :
        pointers = [self._TEE] * (len(contents) - 1) + [self._LAST]
        for pointer, path in zip(pointers, contents):
            yield f'{prefix}{pointer}{path.name}'

            # NOTE: extend the prefix and recurse:
            if path.is_dir(): 
                # NOTE: space because last, └── , above so no more |
                extension = self._BRANCH if pointer == self._TEE else self._SPACE 
                
                yield from self.make_tree(path, prefix=f'{prefix}{extension}')

    def get_tree_lines(self, dirname:Optional[str]=None) -> List[str]:
        dirname = self.prepare_dirname(dirname)
        tree = self.make_tree(dirname)
        lines = [line for line in tree]
        return lines

    def make_tree_str(self, dirname:Optional[str]=None) -> str:
        dirname = self.prepare_dirname(dirname)
        lines = self.get_tree_lines(dirname)
        tree_str = '\n'.join([str(dirname), *lines])
        return tree_str
        
    def prepare_dirname(self, dirname:Optional[str]=None) -> Path:
        if dirname is None:
            dirname = self.dirname

        dirname = os.path.expanduser(dirname) 
        dirname = os.path.abspath(dirname) 

        if not isinstance(dirname, Path):
            dirname = Path(dirname)

        return dirname

    def print(self, dirname:Optional[str]=None) -> None:
        dirname = self.prepare_dirname(dirname)
        tree_str = self.make_tree_str(dirname)
        print(tree_str)
        return

    def __repr__(self):
        dirname = self.dirname
        dirname = self.prepare_dirname(dirname)
        tree_str = self.make_tree_str(dirname)        
        return tree_str        

# %% ../nbs/02_utils.ipynb 42
import os
from pathlib import Path
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, List, ClassVar

# %% ../nbs/02_utils.ipynb 44
import pandas as pd

# %% ../nbs/02_utils.ipynb 45
from iza.static import (
    ADATA, MATRIX, BARCODES, FEATURES, EXT_H5, EXT_MTX, EXT_TSV,
    GENE_SYMBOL, ENSEMBL_ID
)
from iza.types import (
    AnnData
)
from tqdm.auto import tqdm

# %% ../nbs/02_utils.ipynb 46
try: 
    import scanpy as sc, scprep

    # NOTE: Directory defined in _02_utils/_02_directory.ipynb
    @dataclass
    class FilterMatrixDirectory(Directory):
        _: KW_ONLY
        ADATA_FILE: ClassVar[str] = f'{ADATA}{EXT_H5}'
        MATRIX_FILE: ClassVar[str] = f'{MATRIX}{EXT_MTX}'
        BARCODES_FILE: ClassVar[str] = f'{BARCODES}{EXT_TSV}'
        FEATURES_FILE: ClassVar[str] = f'{FEATURES}{EXT_TSV}'
        

        def __post_init__(self):    
            try:
                if not self.has_adata:
                    self.make_adata()
            except Exception as err:
                raise err

        def __repr__(self):
            base = os.path.basename(self.dirname)
            srep = f'FilteredMatrix(valid: {self.is_valid}, adata: {self.has_adata})'        
            srep += '\n'
            srep += super(FilterMatrixDirectory, self).__repr__()
            return srep
                    
        @property
        def adata_filename(self) -> str:
            return os.path.join(self.dirname, self.ADATA_FILE)

        @property
        def matrix_filename(self) -> str:
            return os.path.join(self.dirname, self.MATRIX_FILE)
        
        @property
        def barcodes_filename(self) -> str:
            return os.path.join(self.dirname, self.BARCODES_FILE)
        
        @property
        def features_filename(self) -> str:
            return os.path.join(self.dirname, self.FEATURES_FILE)

        @property
        def has_adata(self) -> bool:
            return os.path.isfile(self.adata_filename)

        @property
        def has_matrix(self) -> bool:
            return os.path.isfile(self.matrix_filename)

        @property
        def has_barcodes(self) -> bool:
            return os.path.isfile(self.barcodes_filename)

        @property
        def has_features(self) -> bool:
            return os.path.isfile(self.features_filename)

        @property
        def is_valid(self) -> bool:
            return all([self.has_matrix, self.has_barcodes, self.has_features])

        def make_adata(self) -> AnnData:
            if self.has_adata:
                return

            steps = (FEATURES, BARCODES, MATRIX, 'combine', ADATA)
            
            desc = os.path.basename(self.dirname)

            steps = tqdm(steps, desc=desc, leave=True)        
            for step in steps:
                steps.set_postfix(stage=step)
                match step:
                    case 'features':
                        features = pd.read_csv(self.features_filename, sep='\t', header=None)
                        features.columns = [ENSEMBL_ID, GENE_SYMBOL, 'feature_type']
                        features.index = pd.Series(features.ensembl_id.copy().values)

                    case 'barcodes':
                        barcodes = pd.read_csv(self.barcodes_filename, sep='\t', header=None)
                        barcodes.columns = [BARCODES]
                        barcodes.index = pd.Series(barcodes.barcodes.copy().values)

                    case 'matrix':
                        matrix = scprep.io.load_mtx(self.matrix_filename, sparse=True).T

                    case 'combine':
                        data = pd.DataFrame.sparse.from_spmatrix(
                            matrix, columns=features.index, index = barcodes.index
                        )
                        del matrix

                    case 'adata':
                        adata = sc.AnnData(X=data.values, obs=barcodes, var=features, dtype='float32')
                        adata.write(self.adata_filename)

                    case _:
                        pass

            return adata

        def get_adata(self) -> AnnData:
            adata = sc.read_h5ad(self.adata_filename)
            return adata

except ImportError as err:
    @dataclass
    class FilterMatrixDirectory(Directory):
        _: KW_ONLY
        ADATA_FILE: ClassVar[str] = f'{ADATA}{EXT_H5}'
        MATRIX_FILE: ClassVar[str] = f'{MATRIX}{EXT_MTX}'
        BARCODES_FILE: ClassVar[str] = f'{BARCODES}{EXT_TSV}'
        FEATURES_FILE: ClassVar[str] = f'{FEATURES}{EXT_TSV}'
        

        def __post_init__(self):    
            raise ImportError('FilterMatrixDirectory requires scprep and scanpy to be installed')
        
    pass

# %% ../nbs/02_utils.ipynb 48
import os
import numpy as np, pandas as pd
from typing import Optional, List, ClassVar, Any

# %% ../nbs/02_utils.ipynb 49
from .types import Tensor, Device, SeriesLike, ndarray

# %% ../nbs/02_utils.ipynb 52
def is_matrix(arr: SeriesLike) -> bool:
    '''
    Checks whether or not `arr` is a np.matrix
    
    Parameters
    ----------    
    arr : SeriesLike
        object to check whether or not it is a np.matrix.
    
    Returns
    -------
    result : bool
    '''
    return isinstance(arr, np.matrix)

def undo_npmatrix(arr: SeriesLike) -> SeriesLike:  
    '''
    Given a tensor converts it to a numpy array
    
    Parameters
    ----------    
    tensor : Tensor
        
    
    Returns
    -------
    arr : ndarray
    
    Notes
    -----
    - several graphtool functions use dependencies which rely on
        the deprecated numpy class `np.matrix`.
        
    - these functions appear to be related to scipy sparse linalg
        methods.
    '''
    if is_matrix(arr):
        return np.array(arr)
    return arr

def is_series(arr: SeriesLike) -> bool:
    '''
    Checks whether or not `arr` is a pd.Series
    
    Parameters
    ----------    
    arr : SeriesLike
        object to check whether or not it is a pd.Series.
    
    Returns
    -------
    result : bool
    '''
    return isinstance(arr, pd.Series)

def is_series_like(series_q: SeriesLike) -> bool:
    '''
    Checks whether or not `series_q` is SeriesLike
    i.e. something that is probably data.
    
    Parameters
    ----------    
    series_q : SeriesLike
        object to check whether or not it is a SeriesLike.
    
    Returns
    -------
    result : bool
    '''
    return isinstance(series_q, SeriesLike)

def is_np(arr_q: SeriesLike) -> bool:
    '''
    Checks whether or not `arr_q` is a ndarray
    
    Parameters
    ----------    
    arr_q : SeriesLike
        object to check whether or not it is a SeriesLike.
    
    Returns
    -------
    result : bool
    '''
    return isinstance(arr_q, ndarray)


# %% ../nbs/02_utils.ipynb 53
def is_device(device_q: Device) -> bool:
    '''
    Checks whether or not `device_q` is a valid
    pytorch device type.
    
    Parameters
    ----------    
    device_q : Device
        object to check whether or not it is a pytorch device.
    
    Returns
    -------
    result : bool        
    
    Notes
    -----
    - There is an execption. `NoneType` is a valid
        pytorch device. Here we return `False` instead.
    '''
    if device_q is None:
        return False
    return isinstance(device_q, Device)

def is_cpu(tensor: Tensor) -> bool:
    '''
    Checks whether or not `tensor` is on cpu
    
    Parameters
    ----------    
    tensor : Tensor
        object to check whether or not it is on cpu.
    
    Returns
    -------
    result : bool
    '''
    # assert is_tensor(tensor)
    if not hasattr(tensor, 'device'):
        return True
    return tensor.device.type == 'cpu'

def is_mps(tensor: Tensor) -> bool:
    '''
    Checks whether or not `tensor` is on cpu
    
    Parameters
    ----------    
    tensor : Tensor
        object to check whether or not it is on cpu.
    
    Returns
    -------
    result : bool
    '''
    # assert is_tensor(tensor)
    if not hasattr(tensor, 'device'):
        return False
    return tensor.device.type == 'mps'

def is_tensor(tensor_q: SeriesLike) -> bool:
    '''
    Checks whether or not `tensor_q` is a pytorch tensor
    
    Parameters
    ----------    
    tensor_q : Tensor
        object to check whether or not it is a pytorch tensor
    
    Returns
    -------
    result : bool
    '''
    return isinstance(tensor_q, Tensor)


def is_torch(tensor_q: SeriesLike) -> bool:
    '''
    Alias for `is_tensor`.
    
    Parameters
    ----------    
    tensor_q : Tensor
        object to check whether or not it is a pytorch tensor
    
    Returns
    -------
    result : bool
    
    See Also
    --------
    is_tensor
    '''
    return is_tensor(tensor_q)

# %% ../nbs/02_utils.ipynb 55
import os, random
import numpy as np

from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, List, ClassVar, Any

# %% ../nbs/02_utils.ipynb 56
from .types import Tensor, Device, SeriesLike, ndarray

# %% ../nbs/02_utils.ipynb 58
try:
    import torch
    def ensure_device(device: Device) -> Device:
        '''
        Given a valid device type attempts to instantiant 
        a pytorch device object i.e. `device='cpu'` will
        return `torch.device('cpu')`.
        
        Parameters
        ----------    
        device : Device
            a valid pytorch device type, possible a string.
        
        Returns
        -------
        device : torch.device        
        
        Raises
        ------
        RuntimeError
            same error if `torch.device(device)` fails
        '''
        if device is None:
            return device    
        try:
            return torch.device(device)
        except RuntimeError as err:
            raise err
        return device
    
    def to_cuda(tensor: Tensor) -> Tensor:
        '''
        Given a tensor, ensures that it is on cuda.
        
        Parameters
        ----------    
        tensor : Tensor
            
        
        Returns
        -------
        tensor : Tensor
        '''
        return tensor.cuda()

    def to_mps(tensor: Tensor) -> Tensor:
        '''
        Given a tensor, ensures that it is on mac silicon.
        
        Parameters
        ----------    
        tensor : Tensor
            
        
        Returns
        -------
        tensor : Tensor
        '''
        return tensor.to(torch.device('mps'))
    
    
    def to_torch(
        arr: SeriesLike,
        cuda: Optional[bool] = False,
        mps: Optional[bool] = False,
        device: Optional[Device] = None,
        dtype: Optional[Any] = None
    ) -> Tensor:
        '''
        Given data, ensures that it is a pytorch Tensor.
        
        Parameters
        ----------    
        arr : SeriesLike
        
        cuda : bool, default=False
            whether to return the tensor on cuda
            
        mps : bool, default=False
            whether to return the tensor on mps
            
        device : Device, optional
            whether to return the tensor on given device
            
        Returns
        -------
        tensor : Tensor
            the input array as a pytorch tensor
            
        Notes
        -----
        - `device` takes priority over `cuda` and `mps`
        '''
        tensor = torch.as_tensor(arr)
        if device is not None:
            tensor = tensor.to(device)
        elif cuda:
            tensor = to_cuda(tensor)
        elif mps:
            tensor = to_mps(tensor)    
        
        if dtype is not None:
            dtype = coerce_mps_dtype(dtype, tensor.device, assume_on_mps=False)
            tensor = tensor.to(dtype)

        return tensor
    
    #| export
    def to_np(tensor:Tensor) -> ndarray:
        '''
        Given a tensor converts it to a numpy array
        
        Parameters
        ----------    
        tensor : Tensor
            
        
        Returns
        -------
        arr : ndarray
        '''
        assert is_tensor(tensor)
        if not hasattr(tensor, 'detach'):
            try:
                return np.array(tensor)
            except Exception as err:
                raise err
        try:
            return tensor.detach().clone().cpu().numpy()
        except Exception as err:
            raise err
    

    def is_mps_available() -> bool:
        '''
        Checks whether or not pytorch has mps availble (version) and was built with mps in mind.

        Returns
        -------
        result : bool
        '''
        maybe_mps = torch.backends.mps.is_available()
        built_mps = torch.backends.mps.is_built()
        return maybe_mps and built_mps
    
    def coerce_mps_dtype(
        dtype, 
        device: Optional[Device] = None, 
        assume_on_mps: Optional[bool] = True
    ):
        '''
        Makes sure `tensor` is `torch.float32` if `tensor.dtype` is `torch.float64`
        if `tensor.device` is `'mps'`.
        
        Parameters
        ----------    
        dtype : any
            dtype to check against
        
        device : Device, default=None
            the device of the tensor or model from which the `dtype` comes from. If provided
            will be used to detemine whether or not to make `torch.float64`, `torch.float32`
            only if the device is actually `'mps'`.

        assume_on_mps: bool, default=True
            whether or not to assume that the device of choice is `'mps'`. Setting this to
            `True` will result in `dtype` of `torch.float64` being converted to `torch.float32`
            to try and silently fix mps errors

        Returns
        -------
        dtype : any
            the dtype, corrected for mps if needed
        '''
        could_be_mps = is_mps_available()
        
        is_float64 = dtype == torch.float64

        if device is not None:
            is_device_mps = device.type == 'mps'
            if is_device_mps:
                assume_on_mps = True

            elif device.type == 'cuda':
                assume_on_mps = False

        
        # NOTE: float64 not availble on mps, coerce to float32
        # NOTE: could_be_mps and assume_on_mps both needed as
        #       device might not be provided.
        if could_be_mps and assume_on_mps and is_float64:
            return torch.float32
        
        return dtype
    
    def ensure_mps_dtype(tensor: Tensor) -> Tensor:
        '''
        Makes sure `tensor` is `torch.float32` if `tensor.dtype` is `torch.float64`
        if `tensor.device` is `'mps'`.
        
        Parameters
        ----------    
        tensor : Tensor
            pytorch tensor to maybe change dtype of
        
        Returns
        -------
        tensor : Tensor
        '''
        dtype = tensor.dtype

        # NOTE: we don't assume mps as we explicitly pass the device
        dtype = coerce_mps_dtype(dtype, tensor.device, assume_on_mps=False)

        tensor = tensor.to(dtype)
        return tensor

    def move_to(
        tensor: Tensor, other: Tensor, 
        dtype: Optional[Any] = None, do_dtype: Optional[bool] = True
    ) -> Tensor:
        '''
        Makes sure `tensor` is on the same device as `other`
        
        Parameters
        ----------    
        tensor : Tensor
            pytorch tensor to change device of
            
        other : Tensor
            pytorch tensor we want `tensor` to be on
            
        dtype : optional
            the data type to make `tensor`. If `None` will infer it
            from `other`
            
        do_dype: bool, default=True
            whether or not to just match the device of `other` or also
            the dtype
        
        Returns
        -------
        tensor : Tensor
        '''
        
        if not is_tensor(tensor):
            tensor = to_torch(tensor)
            
        # NOTE: dtype not provided, so we will infer it
        if dtype is None:
            # NOTE: this little line solves mps float64 issues since 
            #       infer our tensor types and move them accordingly
            other = ensure_mps_dtype(other)
            dtype = other.dtype

        if do_dtype:
            tensor = tensor.to(dtype)

        tensor = tensor.to(other.device)
        
        return tensor

except ImportError as err:
    identity = lambda x: x
    ensure_device = identity
    to_cuda = identity
    to_mps = identity
    to_torch = lambda arr, cuda, mps, device, dtype: arr
    to_np = identity
    is_mps_available = lambda: False
    coerce_mps_dtype = lambda dtype, device, assume_on_mps: dtype
    ensure_mps_dtype = identity
    move_to = lambda tensor, other, dtype, do_dtype: tensor
    pass



# %% ../nbs/02_utils.ipynb 59
try:
    import torch, pytorch_lightning as pl
    def set_seeds(seed: int) -> None:
        '''
        Calls a bunch of seed functions with `seed`
        
        Parameters
        ----------
        seed : int
        '''    
        torch.manual_seed(seed)
        random.seed(seed)
        np.random.seed(seed)    
        pl.seed_everything(seed)
except ImportError as err:
     def set_seeds(seed: int) -> None:
         random.seed(seed)
         np.random.seed(seed)

# %% ../nbs/02_utils.ipynb 61
import os, yaml, datetime, logging

# %% ../nbs/02_utils.ipynb 62
def config_exp_logger(path):
    '''
    Arguments:
    ----------
        path (str): full path to experiment, i.e. 
            `<path-to-experiments-dir>/<experiment-timestamp>`
    Returns:
    ----------
        logger
    '''
    basename = os.path.basename(path)
    logger = logging.getLogger(basename)

    logging.basicConfig(
        filename=exp_log_filename(path), 
        encoding='utf-8',
        level=logging.DEBUG,
        format='%(asctime)s\t%(levelname)s:%(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p',
        filemode='w'
    )
    logger.info(f'Experiment path created {path}')
    return logger

def exp_log_filename(path):
    '''
    Arguments:
    ----------
        path (str): full path to experiment, i.e. 
            `<path-to-experiments-dir>/<experiment-timestamp>`
    Returns:
    ----------
        log_file (str): full path to provided experiment's log file
    '''
    return os.path.join(path, 'log.txt')

def exp_param_filename(path):
    '''
    Arguments:
    ----------
        path (str): full path to experiment, i.e. 
            `<path-to-experiments-dir>/<experiment-timestamp>`
    Returns:
    ----------
        param_file (str): full path to provided experiment's parameter file
    '''
    return os.path.join(path, 'params.yml')

def list_exps(path):
    '''
    Notes:
    ----------
        - an experiment is defined as a directory containing a `'params.yml'` file.
    Arguments:
    ----------
        path (str): full path to experiments directory, i.e. 
            `<path-to-experiments-dir>`
    Returns:
    ----------
        experiments (str[]): experiments (subdirectories) in the specified 
            `path`.
    '''
    test_fn = lambda el: os.path.isdir(el) and os.path.isfile(exp_param_filename(el))
    return list(filter(test_fn, os.listdir(path)))

def gen_exp_name(name=None):
    '''    
    Returns:
    ----------
        exp_name (str): timestamp to serve as experiment name
    '''
    if name is None:
        now =  datetime.datetime.now()
        return now.strftime("%Y_%m_%d-%I_%M_%S_%p")
    return name
        
def load_exp_params(path):
    '''
    Arguments:
    ----------
        path (str): full path to experiment, i.e. 
            `<path-to-experiments-dir>/<experiment-timestamp>`
    Returns:
    ----------
        params (dict): the loaded parameters
    '''
    with open(exp_param_filename(path)) as f:
        return yaml.safe_load(f)
    

def save_exp_params(path, params, logger=None):
    '''
    Arguments:
    ----------
        path (str): full path to experiment, i.e. 
            `<path-to-experiments-dir>/<experiment-timestamp>`
        params (dict): dictionary of parameters to save
        logger (logging.Logger): Defaults to None.
    '''
    with open(exp_param_filename(path), 'w') as f:
        yaml.dump(params, f, default_flow_style=False)
    if logger: 
        logger.info('Experiment parameters saved.')

def setup_exp(path, params, name=None):
    '''
    Arguments:
    ----------
        path (str): full path to where to create experiments, i.e. 
            `<path-to-experiments-dir>`
        params (dict): dictionary of parameters to save
    Returns:
    ----------
        exp_dir (str): full path to experiment, i.e. 
            `<path-to-experiments-dir>/<experiment-timestamp>`
        logger (logging.Logger)
    '''
    exp_name = gen_exp_name(name)
    exp_dir = os.path.join(path, exp_name)
    if not os.path.isdir(exp_dir):
        os.makedirs(exp_dir)

    logger = config_exp_logger(exp_dir)    
    save_exp_params(exp_dir, params, logger)
    return exp_dir, logger

    
def is_config_subset(truth, params):
    '''
    Arguments:
    ----------
        truth (dict): dictionary of parameters to compare to
        params (dict): dictionary of parameters to test
    Returns:
    ----------
        result (bool) whether or not `params` is a subset of `truth`
    '''
    if not type(truth) == type(params): return False
    for key, val in params.items():
        if key not in truth: return False
        if type(val) is dict:
            if not is_config_subset(truth[key], val): 
                return False
        else:            
            if not truth[key] == val: return False
    return True


def find_exps(path, params):
    '''
    Arguments:
    ----------
        path (str): full path to where to create experiments, i.e. 
            `<path-to-experiments-dir>`
        params (dict): dictionary of parameters to test
    Returns:
    ----------
        results (str[]) list of experiment names where their parameters are 
            supersets of the provided `params`
    '''
    exps = list_exps(path)
    results = []
    for exp in exps:
        exp_name = os.path.join(path, exp)
        exp_params = load_exp_params(exp_param_filename(exp_name))
        if is_config_subset(exp_params, params):
            results.append(exp)
    return results
