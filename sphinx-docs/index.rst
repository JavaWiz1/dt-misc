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
   * - :mod:`~dt_tools.logger.logging_helper`
     - Standardize logger (loguru) initialization and properties.
   * - :mod:`~dt_tools.logger.logging_helper_legacy`
     - Standardize logger (python) initialization and properties.
   * - :mod:`~dt_tools.os.os_helper`
     - OS routines for identifying and working with Linux and Windows.
   * - :mod:`~dt_tools.os.sound`
     - Routines for speaking text strings and contents of text files.


.. toctree::
   :maxdepth: 4
   :caption: Contents:

   dt_tools
