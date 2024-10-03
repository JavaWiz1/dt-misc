.. dt-misc documentation master file, created by
   sphinx-quickstart on Thu Aug  8 09:27:19 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

dt-misc documentation
=====================

**dt-misc** is a set of common utilities leverage by dt_tools packages (dt-console, dt-net, dt-pinger,...).  

These can also be incorporated into your project to facilitate logging and os interaction.

Includes:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Package
     - Description
   * - :mod:`~dt_tools.misc.census_geoloc`
     - GeoLoc routines via Census data (address to lat/lon)
   * - :mod:`~dt_tools.misc.geoloc`
     - GeoLoc routines via geocode.maps.co API
   * - :mod:`~dt_tools.misc.sound`
     - Helper routines for Text-to-Speech (TSS).  Requires VLC.
   * - :mod:`~dt_tools.misc.weather`
     - Routines for weather information (current, forecast, alerts)


.. toctree::
   :maxdepth: 4
   :caption: Contents:

   dt_tools
