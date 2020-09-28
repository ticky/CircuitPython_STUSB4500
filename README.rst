Introduction
============

.. image:: https://readthedocs.org/projects/circuitpython-stusb4500/badge/?version=latest
    :target: https://circuitpython-stusb4500.readthedocs.io/
    :alt: Documentation Status

.. image:: https://github.com/ticky/CircuitPython_STUSB4500/workflows/Build%20CI/badge.svg
    :target: https://github.com/ticky/CircuitPython_STUSB4500/actions
    :alt: Build Status

CircuitPython driver for STUSB4500 USB Power Delivery board.

Implementation Notes
--------------------

Based on `SparkFun's Arduino library
<https://github.com/sparkfun/SparkFun_STUSB4500_Arduino_Library>`_.
Further information and notes from `the ST reference implementation
<https://github.com/usb-c/STUSB4500>`_.
Python library and project structure inspired by
`Adafruit's VEML7700 library
<https://github.com/adafruit/Adafruit_CircuitPython_VEML7700>`_,
and Adafruit's other such libraries.

Hardware
--------

* `SparkFun STUSB4500 <https://www.sparkfun.com/products/15801>`_

Dependencies
============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_.

Usage Example
=============

.. literalinclude:: ../examples/stusb4500_simpletest.py
    :caption: examples/stusb4500_simpletest.py
    :linenos:

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/ticky/CircuitPython_STUSB4500/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building
========

This library, along with dependencies and user code, can be too large to be useful on M0 boards like the Trinket M0. Built versions should show up once CI is configured and I've tagged a version, but for both your and my own development purposes I'm documenting how to just get an mpy file here.

You will need to install Adafruit's mpy-cross compiler, either `Adafruit's built version <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/creating-a-library#mpy-2982472-11>`_ or on macOS you can install via `Homebrew <https://brew.sh>`_ by running ``brew install ticky/utilities/circuitpython``.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
