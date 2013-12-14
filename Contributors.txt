Contributors
============

Olof Bjarnason
* Initial proof-of-concept pygame implementation

Fredrik Wendt
* Help with Tkinter implementation (replacing the pygame dependency)

Krunoslav Saho
* Added always-on-top to the pytddmon window

Samuel Ytterbrink
* Print(".") will not screw up test-counting (it did before)
* Docstring support
* Recursive discovery of tests
* Refactoring to increase Pylint score from 6 to 9.5 out of 10 (!)
* Numerous refactorings & other improvements

Rafael Capucho
* Python shebang at start of script, enabling "./pytddmon.py" on unix systems

Ilian Iliev
* Use integers instead of floats in file modified time (checksum calc)
* Auto-update of text in Details window when the log changes

Henrik Bohre
* Status bar in pytddmon window, showing either last time tests were run, or "Testing..." during a test run

Wari Wahab
* PEP 8 fixes and spelling changes
* Travis CI support

Maximilien Riehl
* pytddmon on PyPI
