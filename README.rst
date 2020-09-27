Introduction
============

.. image:: https://readthedocs.org/projects/circuitpython-stusb4500/badge/?version=latest
    :target: https://circuitpython-stusb4500.readthedocs.io/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/ticky/CircuitPython_STUSB4500/workflows/Build%20CI/badge.svg
    :target: https://github.com/ticky/CircuitPython_STUSB4500/actions
    :alt: Build Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

CircuitPython driver for STUSB4500 USB Power Delivery board.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_.

Usage Example
=============

.. todo:: Add a quick, simple example. It and other examples should live in the examples folder and be included in docs/examples.rst.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/ticky/CircuitPython_STUSB4500/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building
========

This library, along with dependencies and user code, can be too large to be useful on M0 boards like the Trinket M0. Built versions should show up once CI is configured and I've tagged a version, but for both your and my own development purposes I'm documenting how to just get an mpy file here.

You will need to install Adafruit's mpy-cross compiler, either `Adafruit's built version <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/creating-a-library#mpy-2982472-11>` or on macOS you can install via `Homebrew <https://brew.sh>` by running "brew install ticky/utilities/circuitpython".

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
