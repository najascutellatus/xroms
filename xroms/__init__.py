"""Initialize xroms."""

from importlib.metadata import PackageNotFoundError, version

from .utilities import (
    argsel2d,
    ddeta,
    ddxi,
    ddz,
    gridmean,
    gridsum,
    hgrad,
    order,
    sel2d,
    subset,
    to_grid,
    to_psi,
    to_rho,
    to_s_rho,
    to_s_w,
    to_u,
    to_v,
    xisoslice,
)
from .derived import (
    EKE,
    KE,
    dudz,
    dvdz,
    ertel,
    relative_vorticity,
    speed,
    uv_geostrophic,
    vertical_shear,
)
from .interp import interpll, isoslice
from .roms_seawater import M2, N2, buoyancy, density, mld, potential_density
from .xroms import open_mfnetcdf, open_netcdf, open_zarr, roms_dataset, grid_interp

import xroms.accessor


try:
    __version__ = version("xroms")
except PackageNotFoundError:
    # package is not installed
    pass

# to manage whether xesmf is installed or not
try:
    import xesmf as xe

    XESMF_AVAILABLE = True
except ImportError:  # pragma: no cover
    XESMF_AVAILABLE = False  # pragma: no cover
