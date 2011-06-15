Q: What is this directory?
A: It contains so-called "system-level" tests for pyTDDmon.

Q: What do you mean, "system level"?
A: It means that they excercise pyTDDmon "as a whole", rather than testing it's parts, as the ordinary unit-tests do (those that are called test_*.py in pyTDDmon root directory)

Q: Why a 'systest' directory? Why not put them among the other test_*.py files?
A: To clearly separate unit-level tests from system-level tests.

Q: How are the system level tests run?
A: The tests in this directory are not meant to be run by pyTDDmon. Run them with the run_all.py script:

$ python run_all.py

It will output which tests worked and which failed.
