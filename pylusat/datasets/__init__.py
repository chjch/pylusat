import os

__all__ = ["available", "get_path"]
_module_path = os.path.dirname(__file__)


def _get_dataset_name_by_type(extension='.shp'):
    names = []
    for root, dirs, files in os.walk(_module_path):
        for file in files:
            if file.endswith(extension):
                names.append(os.path.basename(root))
    return names


_available_shp = _get_dataset_name_by_type('.shp')
_available_tif = _get_dataset_name_by_type('.tif')

available = _available_shp + _available_tif


def get_path(dataset):
    """
    Get the path to the data file.
    Parameters
    ----------
    dataset : str
        The name of the dataset. See ``pylusat.datasets.available`` for
        all options.
    Examples
    --------
    >>> pylusat.datasets.get_path("acs2016") # doctest: +SKIP
    '.../python3.6/site-packages/pylusat/datasets/acs2016/acs2016.shp'
    """
    if dataset in _available_shp:
        return os.path.abspath(os.path.join(_module_path,
                                            dataset,
                                            dataset + ".shp"))
    elif dataset in _available_tif:
        return os.path.abspath(os.path.join(_module_path,
                                            dataset,
                                            dataset + ".tif"))
    else:
        msg = "The dataset '{data}' is not available. ".format(data=dataset)
        msg += "Available datasets are {}".format(", ".join(available))
        raise ValueError(msg)
