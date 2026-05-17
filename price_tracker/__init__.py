# -*- coding: utf-8 -*-
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8
    from importlib_metadata import version, PackageNotFoundError

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'price-tracker'
    __version__ = version(dist_name)
except PackageNotFoundError:
    __version__ = 'unknown'
