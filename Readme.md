pytddmon - continuous unit testing in Python
============================================
[![Travis CI status](https://api.travis-ci.org/objarni/pytddmon.png)](https://travis-ci.org/objarni/pytddmon)

Latest news
-----------
Read the pytddmon blog and more documentation at

http://pytddmon.org


How to use
---------------

### From the cheeseshop

Install `pytddmon` from PyPI:
```bash
pip install pytddmon
```

You can now run `pytddmon.py` from anywhere.

### Run from sources

Copy `src/pytddmon.py` to your projects' root folder. From there, type:

           python pytddmon.py


License
-------
See License.txt. Basically MIT / do whatever.


Folder structure
----------------
           src/       contains pytddmon.py
           src/tests  unit tests for pytddmon.py
           logo/      pytddmon logo
           systest/   contains systest.py, lots of folders and a Readme.txt
                      (used for end-to-end regression testing pytddmon.py)

Submitting a patch
------------------
TravisCI is used for automatic unit and integration testing when a pull request arrives at Github.

However, you may want to run the automatic tests locally before requesting a pull.

### Running the unit tests

           cd pytddmon/src
           python pytddmon.py


### Running the integration tests

           cd pytddmon/systest
           python systest.py

