"""
This is an accessor to xarray. It is basically a convenient way to
use some of the xroms functions, which has bookkeeping in the
background where possible. No functions are available only here;
this connects to functions in other files.
"""

import numpy as np
import xarray as xr

# from xgcm import grid

# import xroms
from .xroms import roms_dataset
from .derived import speed, KE, uv_geostrophic, EKE, dudz, dvdz, vertical_shear, relative_vorticity, ertel, w, omega
from .interp import isoslice, interpll
from .roms_seawater import density, potential_density, buoyancy, N2, M2, mld
from .utilities import order, gridsum, gridmean, sel2d, argsel2d, ddxi, ddeta, ddz, to_grid, subset

xr.set_options(keep_attrs=True)

g = 9.81  # m/s^2


@xr.register_dataset_accessor("xroms")
class xromsDatasetAccessor:
    """Accessor for Datasets."""

    def __init__(self, ds):

        self.ds = ds

        # extra for getting coordinates but changes variables
        self._ds = ds.copy(deep=True)

        # self.ds, xgrid = xroms.roms_dataset(self.ds)

    def set_grid(self, xgrid):
        """If you already have a xgrid object and don't want to rerun

        Or, you want to have more options in the xgrid setup, input it to the xroms accessor this way.

        Examples
        --------
        >>> ds.xroms.set_grid(xgrid)
        """
        self._xgrid = xgrid

    @property
    def xgrid(self):
        if not hasattr(self, "_xgrid"):
            self.ds, xgrid = roms_dataset(self.ds)
            self._xgrid = xgrid
        return self._xgrid

    @property
    def speed(self):
        """Calculate horizontal speed [m/s] from u and v components, on rho/rho grids.

        Notes
        -----
        speed = np.sqrt(u^2 + v^2)

        Uses 'extend' for horizontal boundary.

        See `xroms.speed` for full docstring.

        Examples
        --------
        >>> ds.xroms.speed
        """

        if "speed" not in self.ds:
            var = speed(self.ds.u, self.ds.v, self.xgrid, hboundary="extend")
            self.ds["speed"] = var
        return self.ds.speed

    @property
    def KE(self):
        """Calculate kinetic energy [kg/(m*s^2)], on rho/rho grids.

        Notes
        -----
        Uses speed that has been extended out to the rho grid and rho0.

        See `xroms.KE` for full docstring.

        Examples
        --------
        >>> ds.xroms.KE
        """

        if "KE" not in self.ds:
            var = KE(self.ds.rho0, self.speed)
            self.ds["KE"] = var
        return self.ds.KE

    @property
    def ug(self):
        """Calculate geostrophic u velocity from zeta, on u grid.

        Notes
        -----
        ug = -g * zeta_xi / (d xi * f)  # on u grid

        See `xroms.uv_geostrophic` for full docstring.

        Examples
        --------
        >>> ds.xroms.ug
        """

        if "ug" not in self.ds:
            ug = uv_geostrophic(
                self.ds.zeta,
                self.ds.f,
                self.xgrid,
                hboundary="extend",
                hfill_value=None,
                which="xi",
            )
            self.ds["ug"] = ug
        return self.ds["ug"]

    @property
    def vg(self):
        """Calculate geostrophic v velocity from zeta, on v grid.

        Notes
        -----
        vg = g * zeta_eta / (d eta * f)  # on v grid

        See `xroms.uv_geostrophic` for full docstring.

        Examples
        --------
        >>> ds.xroms.vg
        """

        if "vg" not in self.ds:
            vg = uv_geostrophic(
                self.ds.zeta,
                self.ds.f,
                self.xgrid,
                hboundary="extend",
                hfill_value=None,
                which="eta",
            )
            self.ds["vg"] = vg
        return self.ds["vg"]

    @property
    def EKE(self):
        """Calculate EKE [m^2/s^2], on rho grid.

        Notes
        -----
        EKE = 0.5*(ug^2 + vg^2)
        Puts geostrophic speed on rho grid.

        See `xroms.EKE` for full docstring.

        Examples
        --------
        >>> ds.xroms.EKE
        """

        if "EKE" not in self.ds:
            var = EKE(self.ug, self.vg, self.xgrid, hboundary="extend")
            self.ds["EKE"] = var
        return self.ds["EKE"]

    @property
    def dudz(self):
        """Calculate dudz [1/s] on u/w grids.

        Notes
        -----
        See `xroms.dudz` for full docstring.

        `sboundary` is set to 'extend'.


        Examples
        --------
        >>> ds.xroms.dudz
        """

        if "dudz" not in self.ds:
            var = dudz(self.ds.u, self.xgrid, sboundary="extend")
            self.ds["dudz"] = var
        return self.ds["dudz"]

    @property
    def dvdz(self):
        """Calculate dvdz [1/s] on v/w grids.

        Notes
        -----
        See `xroms.dvdz` for full docstring.

        `sboundary` is set to 'extend'.


        Examples
        --------
        >>> ds.xroms.dvdz
        """

        if "dvdz" not in self.ds:
            var = dvdz(self.ds.v, self.xgrid, sboundary="extend")
            self.ds["dvdz"] = var
        return self.ds["dvdz"]

    @property
    def vertical_shear(self):
        """Calculate vertical shear [1/s], rho/w grids.

        Notes
        -----
        See `xroms.vertical_shear` for full docstring.

        `hboundary` is set to 'extend'.

        Examples
        --------
        >>> ds.xroms.vertical_shear
        """

        if "shear" not in self.ds:
            var = vertical_shear(
                self.dudz, self.dvdz, self.xgrid, hboundary="extend"
            )
            self.ds["shear"] = var
        return self.ds["shear"]

    @property
    def vort(self):
        """Calculate vertical relative vorticity, psi/w grids.

        Notes
        -----
        See `xroms.relative_vorticity` for full docstring.

        `hboundary` and `sboundary` both set to 'extend'.

        Examples
        --------
        >>> ds.xroms.vort
        """

        if "vort" not in self.ds:
            var = relative_vorticity(
                self.ds.u, self.ds.v, self.xgrid, hboundary="extend", sboundary="extend"
            )
            self.ds["vort"] = var
        return self.ds.vort

    @property
    def ertel(self):
        """Calculate Ertel potential vorticity of buoyancy on rho/rho grids.

        Notes
        -----
        See `xroms.ertel` for full docstring.

        `hboundary` and `sboundary` both set to 'extend'.

        Examples
        --------
        >>> ds.xroms.ertel
        """

        if "ertel" not in self.ds:
            var = ertel(
                self.buoyancy,
                self.ds.u,
                self.ds.v,
                self.ds.f,
                self.xgrid,
                hcoord="rho",
                scoord="s_rho",
                hboundary="extend",
                hfill_value=None,
                sboundary="extend",
                sfill_value=None,
            )
            self.ds["ertel"] = var
        return self.ds.ertel

    @property
    def w(self):
        """Calculate vertical velocity on [horizontal]/[vertical] grids.

        Notes
        -----
        See `xroms.w` for full docstring.

        Examples
        --------
        >>> ds.xroms.w
        """

        return w(self.ds.u, self.ds.v)

    @property
    def omega(self):
        """Calculate s-grid vertical velocity on [horizontal]/[vertical] grids.

        Notes
        -----
        See `xroms.omega` for full docstring.

        Examples
        --------
        >>> ds.xroms.omega
        """

        return omega(self.ds.u, self.ds.v)

    @property
    def rho(self):
        """Return existing rho or calculate, on rho/rho grids.

        Notes
        -----
        See `xroms.density` for full docstring.

        Examples
        --------
        >>> ds.xroms.rho
        """

        if "rho" not in self.ds:
            var = density(self.ds.temp, self.ds.salt, self.ds.z_rho)
            self.ds["rho"] = var

        return self.ds.rho

    @property
    def sig0(self):
        """Calculate potential density referenced to z=0, on rho/rho grids.

        Notes
        -----
        See `xroms.potential_density` for full docstring.

        Examples
        --------
        >>> ds.xroms.sig0
        """

        if "sig0" not in self.ds:
            var = potential_density(self.ds.temp, self.ds.salt, 0)
            self.ds["sig0"] = var
        return self.ds.sig0

    @property
    def buoyancy(self):
        """Calculate buoyancy on rho/rho grids.

        Notes
        -----
        See `xroms.buoyancy` for full docstring.

        Examples
        --------
        >>> ds.xroms.buoyancy
        """

        if "buoyancy" not in self.ds:
            var = buoyancy(self.sig0, self.ds.rho0)
            self.ds["buoyancy"] = var
        return self.ds.buoyancy

    @property
    def N2(self):
        """Calculate buoyancy frequency squared on rho/w grids.

        Notes
        -----
        See `xroms.N2` for full docstring.

        `sboundary` set to 'fill' with `sfill_value=np.nan`.

        Examples
        --------
        >>> ds.xroms.N2
        """

        if "N2" not in self.ds:
            var = N2(
                self.rho, self.xgrid, self.ds.rho0, sboundary="fill", sfill_value=np.nan
            )
            self.ds["N2"] = var
        return self.ds.N2

    @property
    def M2(self):
        """Calculate the horizontal buoyancy gradient on rho/w grids.

        Notes
        -----
        See `xroms.M2` for full docstring.

        `hboundary` set to 'extend' and `sboundary='fill'` with `sfill_value=np.nan`.

        Examples
        --------
        >>> ds.xroms.M2
        """

        if "M2" not in self.ds:
            var = M2(
                self.rho,
                self.xgrid,
                self.ds.rho0,
                hboundary="extend",
                sboundary="fill",
                sfill_value=np.nan,
            )
            self.ds["M2"] = var
        return self.ds.M2

    def mld(self, thresh=0.03):
        """Calculate mixed layer depth [m] on rho grid.

        Inputs
        ------
        thresh: float, optional
            Threshold for detection of mixed layer [kg/m^3]

        Notes
        -----
        See `xroms.mld` for full docstring.

        Examples
        --------
        >>> ds.xroms.mld(thresh=0.03).isel(ocean_time=0).plot(vmin=-20, vmax=0)
        """

        return mld(
            self.sig0, self.xgrid, self.ds.h, self.ds.mask_rho, thresh=thresh
        )

    def ddxi(
        self,
        varname,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
        attrs=None,
    ):
        """Calculate d/dxi for a variable.

        Parameters
        ----------
        varname: str
            Name of variable in Dataset to operate on.
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for calculating horizontal derivative of var. This same value
            will be used for all horizontal grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection
            for calculating horizontal derivative of var. This same value will
            be used for all vertical grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        attrs: dict, optional
            Dictionary of attributes to add to resultant arrays. Requires that
            q is DataArray. For example:
            `attrs={'name': 'varname', 'long_name': 'longvarname', 'units': 'units'}`

        Returns
        -------
        DataArray of dqdxi, the gradient of q in the xi-direction with
        attributes altered to reflect calculation.

        Notes
        -----
        dqdxi = dqdx*dzdz - dqdz*dzdx

        Derivatives are taken in the ROMS curvilinear grid native xi-direction.

        These derivatives properly account for the fact that ROMS vertical coordinates are
        s coordinates and therefore can vary in time and space.

        This will alter the number of points in the xi and s dimensions.

        Examples
        --------
        >>> ds.xroms.ddxi('salt')
        """

        assert isinstance(
            varname, str
        ), "varname should be a string of the name of a variable stored in the Dataset"
        assert varname in self.ds, 'variable called "varname" must be in Dataset'
        var = ddxi(
            self.ds[varname],
            self.xgrid,
            attrs=attrs,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
        )

        self._ds[var.name] = var
        return self._ds[var.name]

    def ddeta(
        self,
        varname,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
        attrs=None,
    ):
        """Calculate d/deta for a variable.

        Parameters
        ----------
        varname: str
            Name of variable in Dataset to operate on.
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for calculating horizontal derivative of var. This same value
            will be used for grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection
            for calculating horizontal derivative of var. This same value will
            be used for grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        attrs: dict, optional
            Dictionary of attributes to add to resultant arrays. Requires that
            q is DataArray. For example:
            `attrs={'name': 'varname', 'long_name': 'longvarname', 'units': 'units'}`

        Returns
        -------
        DataArray of dqdeta, the gradient of q in the eta-direction with
        attributes altered to reflect calculation.

        Notes
        -----
        dqdeta = dqdy*dzdz - dqdz*dzdy

        Derivatives are taken in the ROMS curvilinear grid native eta-direction.

        These derivatives properly account for the fact that ROMS vertical coordinates are
        s coordinates and therefore can vary in time and space.

        This will alter the number of points in the eta and s dimensions.

        Examples
        --------
        >>> ds.xroms.ddeta('salt')
        """

        assert isinstance(
            varname, str
        ), "varname should be a string of the name of a variable stored in the Dataset"
        assert varname in self.ds, 'variable called "varname" must be in Dataset'
        var = ddeta(
            self.ds[varname],
            self.xgrid,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
            attrs=attrs,
        )

        self._ds[var.name] = var
        return self._ds[var.name]

    def ddz(
        self,
        varname,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
        attrs=None,
    ):
        """Calculate d/dz for a variable.

        Parameters
        ----------
        varname: str
            Name of variable in Dataset to operate on.
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for grid changes.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection for
            calculating z derivative. This same value will be used for grid
            changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary fill value
            associated with sboundary input.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        attrs: dict, optional
            Dictionary of attributes to add to resultant arrays. Requires that
            q is DataArray. For example:
            `attrs={'name': 'varname', 'long_name': 'longvarname', 'units': 'units'}`

        Returns
        -------
        DataArray of vertical derivative of variable with
        attributes altered to reflect calculation.

        Notes
        -----
        This will alter the number of points in the s dimension.

        Examples
        --------
        >>> ds.xroms.ddz('salt')
        """

        assert isinstance(
            varname, str
        ), "varname should be a string of the name of a variable stored in the Dataset"
        assert varname in self.ds, 'variable called "varname" must be in Dataset'
        var = ddz(
            self.ds[varname],
            self.xgrid,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
            attrs=attrs,
        )

        self._ds[var.name] = var
        return self._ds[var.name]

    def to_grid(
        self,
        varname,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
    ):
        """Implement grid changes.

        Parameters
        ----------
        varname: str
            Name of variable in Dataset to operate on.
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for grid changes.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection
            for grid changes.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.

        Returns
        -------
        DataArray interpolated onto hcoord horizontal and scoord
        vertical grids.

        Notes
        -----
        If var is already on selected grid, nothing happens.

        Examples
        --------
        >>> ds.xroms.to_grid('salt', hcoord='rho', scoord='w')
        """

        assert isinstance(
            varname, str
        ), "varname should be a string of the name of a variable stored in the Dataset"
        assert varname in self.ds, 'variable called "varname" must be in Dataset'
        var = to_grid(
            self.ds[varname],
            self.xgrid,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
        )

        self._ds[var.name] = var
        return self._ds[var.name]

    def subset(self, X=None, Y=None):
        """Subset model output horizontally using isel, properly accounting for horizontal grids.

        Parameters
        ----------
        X: slice, optional
            Slice in X dimension using form `X=slice(start, stop, step)`. For example,
            >>> X=slice(20,40,2)
            Indices are used for rho grid, and psi grid is reduced accordingly.
        Y: slice, optional
            Slice in Y dimension using form `Y=slice(start, stop, step)`. For example,
            >>> Y=slice(20,40,2)
            Indices are used for rho grid, and psi grid is reduced accordingly.

        Returns
        -------
        Dataset with form as if model had been run at the subsetted size. That is, the outermost
        cells of the rho grid are like ghost cells and the psi grid is one inward from this size
        in each direction.

        Notes
        -----
        X and Y must be slices, not single numbers.

        Examples
        --------
        Subset only in Y direction:
        >>> ds.xroms.subset(Y=slice(50,100))
        Subset in X and Y:
        >>> ds.xroms.subset(X=slice(20,40), Y=slice(50,100))
        """

        return subset(self.ds, X=X, Y=Y)


@xr.register_dataarray_accessor("xroms")
class xromsDataArrayAccessor:
    """Accessor for DataArrays."""

    def __init__(self, da):

        self.da = da

        # # make copy of ds that I can use to stash DataArrays to
        # # retrieve coords without changing original ds.
        # self.ds = self.da.attrs["grid"]._ds.copy(deep=True)

    def to_grid(
        self,
        xgrid,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
    ):
        """Implement grid changes.

        Parameters
        ----------
        xgrid:
            xgcm grid
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for grid changes.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection
            for grid changes.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.

        Returns
        -------
        DataArray interpolated onto hcoord horizontal and scoord
        vertical grids.

        Notes
        -----
        If var is already on selected grid, nothing happens.

        Examples
        --------
        >>> ds.salt.xroms.to_grid(xgrid, hcoord='rho', scoord='w')
        """

        raise KeyError(
            "Other coordinates are not available on DataArray, so this transformation is only possible on Dataset."
        )

        var = xroms.to_grid(
            self.da,
            xgrid,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
        )
        self.ds[var.name] = var
        return self.ds[var.name]

    def ddz(
        self,
        xgrid,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
        attrs=None,
    ):
        """Calculate d/dz for a variable.

        Parameters
        ----------
        xgrid
            xgcm grid
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for grid changes.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection for
            calculating z derivative. This same value will be used for grid
            changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary fill value
            associated with sboundary input.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        attrs: dict, optional
            Dictionary of attributes to add to resultant arrays. Requires that
            q is DataArray. For example:
            `attrs={'name': 'varname', 'long_name': 'longvarname', 'units': 'units'}`

        Returns
        -------
        DataArray of vertical derivative of variable with
        attributes altered to reflect calculation.

        Notes
        -----
        This will alter the number of points in the s dimension.

        Examples
        --------
        >>> ds.salt.xroms.ddz(xgrid)
        """

        raise KeyError(
            "Other coordinates are not available on DataArray, so this transformation is only possible on Dataset."
        )

        var = xroms.ddz(
            self.da,
            xgrid,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
            attrs=attrs,
        )
        self.ds[var.name] = var
        return self.ds[var.name]

    def ddxi(
        self,
        xgrid,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
        attrs=None,
    ):
        """Calculate d/dxi for variable.

        Parameters
        ----------
        xgrid
            xgcm grid
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for calculating horizontal derivative of var. This same value
            will be used for all horizontal grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection
            for calculating horizontal derivative of var. This same value will
            be used for all vertical grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        attrs: dict, optional
            Dictionary of attributes to add to resultant arrays. Requires that
            q is DataArray. For example:
            `attrs={'name': 'varname', 'long_name': 'longvarname', 'units': 'units'}`

        Returns
        -------
        DataArray of dqdxi, the gradient of q in the xi-direction with
        attributes altered to reflect calculation.

        Notes
        -----
        dqdxi = dqdx*dzdz - dqdz*dzdx

        Derivatives are taken in the ROMS curvilinear grid native xi-direction.

        These derivatives properly account for the fact that ROMS vertical coordinates are
        s coordinates and therefore can vary in time and space.

        This will alter the number of points in the xi and s dimensions.

        Examples
        --------
        >>> ds.salt.xroms.ddxi(xgrid)
        """

        raise KeyError(
            "Other coordinates are not available on DataArray, so this transformation is only possible on Dataset."
        )

        var = xroms.ddxi(
            self.da,
            xgrid,
            attrs=attrs,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
        )
        self.ds[var.name] = var
        return self.ds[var.name]

    def ddeta(
        self,
        xgrid,
        hcoord=None,
        scoord=None,
        hboundary="extend",
        hfill_value=None,
        sboundary="extend",
        sfill_value=None,
        attrs=None,
    ):
        """Calculate d/deta for a variable.

        Parameters
        ----------
        xgrid
            xgcm grid
        hcoord: string, optional.
            Name of horizontal grid to interpolate output to.
            Options are 'rho', 'psi', 'u', 'v'.
        scoord: string, optional.
            Name of vertical grid to interpolate output to.
            Options are 's_rho', 's_w', 'rho', 'w'.
        hboundary: string, optional
            Passed to `grid` method calls; horizontal boundary selection
            for calculating horizontal derivative of var. This same value
            will be used for grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        hfill_value: float, optional
            Passed to `grid` method calls; horizontal boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        sboundary: string, optional
            Passed to `grid` method calls; vertical boundary selection
            for calculating horizontal derivative of var. This same value will
            be used for grid changes too.
            From xgcm documentation:
            A flag indicating how to handle boundaries:
            * None:  Do not apply any boundary conditions. Raise an error if
              boundary conditions are required for the operation.
            * 'fill':  Set values outside the array boundary to fill_value
              (i.e. a Neumann boundary condition.)
            * 'extend': Set values outside the array to the nearest array
              value. (i.e. a limited form of Dirichlet boundary condition.
        sfill_value: float, optional
            Passed to `grid` method calls; vertical boundary selection
            fill value.
            From xgcm documentation:
            The value to use in the boundary condition with `boundary='fill'`.
        attrs: dict, optional
            Dictionary of attributes to add to resultant arrays. Requires that
            q is DataArray. For example:
            `attrs={'name': 'varname', 'long_name': 'longvarname', 'units': 'units'}`

        Returns
        -------
        DataArray of dqdeta, the gradient of q in the eta-direction with
        attributes altered to reflect calculation.

        Notes
        -----
        dqdeta = dqdy*dzdz - dqdz*dzdy

        Derivatives are taken in the ROMS curvilinear grid native eta-direction.

        These derivatives properly account for the fact that ROMS vertical coordinates are
        s coordinates and therefore can vary in time and space.

        This will alter the number of points in the eta and s dimensions.

        Examples
        --------
        >>> ds.salt.xroms.ddeta(xgrid)
        """

        raise KeyError(
            "Other coordinates are not available on DataArray, so this transformation is only possible on Dataset."
        )

        var = xroms.ddeta(
            self.da,
            xgrid,
            attrs=attrs,
            hcoord=hcoord,
            scoord=scoord,
            hboundary=hboundary,
            hfill_value=hfill_value,
            sboundary=sboundary,
            sfill_value=sfill_value,
        )
        self.ds[var.name] = var
        return self.ds[var.name]

    def argsel2d(self, lon0, lat0):
        """Find the indices of coordinate pair closest to another point.

        Parameters
        ----------
        lon0: float, int
            Longitude of comparison point.
        lat0: float, int
            Latitude of comparison point.

        Returns
        -------
        Indices in eta, xi of closest location to lon0, lat0.

        Notes
        -----
        This function uses Great Circle distance to calculate distances assuming
        longitudes and latitudes as point coordinates. Uses cartopy function
        `Geodesic`: https://scitools.org.uk/cartopy/docs/latest/cartopy/geodesic.html

        Examples
        --------
        >>> ds.temp.xroms.argsel2d(-96, 27)
        """

        return argsel2d(
            self.da.cf["longitude"], self.da.cf["latitude"], lon0, lat0
        )

    def sel2d(self, lon0, lat0):
        """Find the value of the var at closest location to lon0,lat0.

        Parameters
        ----------
        lon0: float, int
            Longitude of comparison point.
        lat0: float, int
            Latitude of comparison point.

        Returns
        -------
        DataArray value(s) of closest location to lon0/lat0.

        Notes
        -----
        This function uses Great Circle distance to calculate distances assuming
        longitudes and latitudes as point coordinates. Uses cartopy function
        `Geodesic`: https://scitools.org.uk/cartopy/docs/latest/cartopy/geodesic.html

        This wraps `argsel2d`.

        Examples
        --------
        >>> ds.temp.xroms.sel2d(-96, 27)
        """

        return sel2d(
            self.da, self.da.cf["longitude"], self.da.cf["latitude"], lon0, lat0
        )

    def gridmean(self, xgrid, dim):
        """Calculate mean accounting for variable spatial grid.

        Parameters
        ----------
        xgrid
            xgcm grid
        dim: str, list, tuple
            Spatial dimension names to average over. In the `xgcm`
            convention, the allowable names are 'Z', 'Y', or 'X'.

        Returns
        -------
        DataArray or ndarray of average calculated over dim accounting
        for variable spatial grid.

        Notes
        -----
        If result is DataArray, long name attribute is modified to describe
        calculation.

        Examples
        --------
        Note that the following two approaches are equivalent:
        >>> app1 = ds.u.xroms.gridmean(xgrid, ('Y','X'))
        >>> app2 = (ds.u*ds.dy_u*ds.dx_u).sum(('eta_rho','xi_u'))/(ds.dy_u*ds.dx_u).sum(('eta_rho','xi_u'))
        >>> np.allclose(app1, app2)
        """

        return gridmean(self.da, xgrid, dim)

    def gridsum(self, xgrid, dim):
        """Calculate sum accounting for variable spatial grid.

        Parameters
        ----------
        xgrid
            xgcm grid
        dim: str, list, tuple
            Spatial dimension names to sum over. In the `xgcm`
            convention, the allowable names are 'Z', 'Y', or 'X'.

        Returns
        -------
        DataArray or ndarray of sum calculated over dim accounting
        for variable spatial grid.

        Notes
        -----
        If result is DataArray, long name attribute is modified to describe
        calculation.

        Examples
        --------
        Note that the following two approaches are equivalent:
        >>> app1 = ds.u.xroms.gridsum(xgrid, ('Z','X'))
        >>> app2 = (ds.u*ds.dz_u * ds.dx_u).sum(('s_rho','xi_u'))
        >>> np.allclose(app1, app2)
        """

        return gridsum(self.da, xgrid, dim)

    def interpll(self, lons, lats, which="pairs"):
        """Interpolate var to lons/lats positions.

        Wraps xESMF to perform proper horizontal interpolation on non-flat Earth.

        Parameters
        ----------
        lons: list, ndarray
            Longitudes to interpolate to. Will be flattened upon input.
        lats: list, ndarray
            Latitudes to interpolate to. Will be flattened upon input.
        which: str, optional
            Which type of interpolation to do:
            * "pairs": lons/lats as unstructured coordinate pairs
              (in xESMF language, LocStream).
            * "grid": 2D array of points with 1 dimension the lons and
              the other dimension the lats.

        Returns
        -------
        DataArray of var interpolated to lons/lats. Dimensionality will be the
        same as var except the Y and X dimensions will be 1 dimension called
        "locations" that lons.size if which=='pairs', or 2 dimensions called
        "lat" and "lon" if which=='grid' that are of lats.size and lons.size,
        respectively.

        Notes
        -----
        var cannot have chunks in the Y or X dimensions.

        cf-xarray should still be usable after calling this function.

        Examples
        --------
        To return 1D pairs of points, in this case 3 points:
        >>> xroms.interpll(var, [-96, -97, -96.5], [26.5, 27, 26.5], which='pairs')
        To return 2D pairs of points, in this case a 3x3 array of points:
        >>> xroms.interpll(var, [-96, -97, -96.5], [26.5, 27, 26.5], which='grid')
        """

        return interpll(self.da, lons, lats, which=which)

    def isoslice(self, xgrid, iso_values, iso_array=None, axis="Z"):
        """Interpolate var to iso_values.

        This wraps `xgcm` `transform` function for slice interpolation,
        though `transform` has additional functionality.

        Parameters
        ----------
        xgrid
            xgcm grid
        iso_values: list, ndarray
            Values to interpolate to. If calculating var at fixed depths,
            iso_values are the fixed depths, which should be negative if
            below mean sea level. If input as array, should be 1D.
        iso_array: DataArray, optional
            Array that var is interpolated onto (e.g., z coordinates or
            density). If calculating var on fixed depth slices, iso_array
            contains the depths [m] associated with var. In that case and
            if None, will use z coordinate attached to var. Also use this
            option if you want to interpolate with z depths constant in
            time and input the appropriate z coordinate.
        dim: str, optional
            Dimension over which to calculate isoslice. If calculating var
            onto fixed depths, `dim='Z'`. Options are 'Z', 'Y', and 'X'.

        Returns
        -------
        DataArray of var interpolated to iso_values. Dimensionality will be the
        same as var except with dim dimension of size of iso_values.

        Notes
        -----
        var cannot have chunks in the dimension dim.

        cf-xarray should still be usable after calling this function.

        Examples
        --------
        To calculate temperature onto fixed depths:
        
        >>> xroms.isoslice(ds.temp, np.linspace(0, -30, 50), xgrid)

        To calculate temperature onto salinity:
        
        >>> xroms.isoslice(ds.temp, np.arange(0, 36), xgrid, iso_array=ds.salt, axis='Z')

        Calculate lat-z slice of salinity along a constant longitude value (-91.5):
        
        >>> xroms.isoslice(ds.salt, -91.5, xgrid, iso_array=ds.lon_rho, axis='X')

        Calculate slice of salt at 28 deg latitude
        
        >>> xroms.isoslice(ds.salt, 28, xgrid, iso_array=ds.lat_rho, axis='Y')

        Interpolate temp to salinity values between 0 and 36 in the X direction
        
        >>> xroms.isoslice(ds.temp, np.linspace(0, 36, 50), xgrid, iso_array=ds.salt, axis='X')

        Interpolate temp to salinity values between 0 and 36 in the Z direction
        
        >>> xroms.isoslice(ds.temp, np.linspace(0, 36, 50), xgrid, iso_array=ds.salt, axis='Z')

        Calculate the depth of a specific isohaline (33):
        
        >>> xroms.isoslice(ds.salt, 33, xgrid, iso_array=ds.z_rho, axis='Z')

        Calculate dye 10 meters above seabed. Either do this on the vertical
        rho grid, or first change to the w grid and then use `isoslice`. You may prefer
        to do the latter if there is a possibility that the distance above the seabed you are
        interpolating to (10 m) could be below the deepest rho grid depth.
        
        * on rho grid directly:
        
        >>> height_from_seabed = ds.z_rho + ds.h
        >>> height_from_seabed.name = 'z_rho'
        >>> xroms.isoslice(ds.dye_01, 10, xgrid, iso_array=height_from_seabed, axis='Z')
        
        * on w grid:
        
        >>> var_w = ds.dye_01.xroms.to_grid(xgrid, scoord='w').chunk({'s_w': -1})
        >>> ds['dye_01_w'] = var_w  # currently this is the easiest way to reattached coords xgcm variables
        >>> height_from_seabed = ds.z_w + ds.h
        >>> height_from_seabed.name = 'z_w'
        >>> xroms.isoslice(ds['dye_01_w'], 10, xgrid, iso_array=height_from_seabed, axis='Z')
        """

        return isoslice(
            self.da,
            iso_values,
            grid=xgrid,
            iso_array=iso_array,
            axis=axis,
        )

    def order(self):
        """Reorder self to typical dimensional ordering.

        Returns
        -------
        DataArray with dimensional order ['T', 'Z', 'Y', 'X'], or whatever subset of
        dimensions are present in var.

        Notes
        -----
        Do not consider previously-selected dimensions that are kept on as coordinates but
        cannot be transposed anymore. This is accomplished with `.reset_coords(drop=True)`.

        Examples
        --------
        >>> ds.temp.xroms.order()
        """

        return order(self.da)
