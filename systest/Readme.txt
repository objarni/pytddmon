Q: What is this directory?
A: It contains so-called "system-level" tests for pyTDDmon.

Q: What do you mean, "system level"?
A: It means that they excercise pytddmon "as a whole", rather than testing it's parts,
as the ordinary unit-tests do (those that are called test_*.py in pytddmon root directory)

Q: Why a 'systest' directory? Why not put them among the other test_*.py files?
A: To clearly separate unit-level tests from system-level tests.

Q: How are the system level tests run?
A: The tests in this directory are not meant to be run by pyTDDmon. Run them with the
run_all.py script:

$ python run_all.py

It will output which tests worked and which failed.

Q: How is this organized?
A: The run_all.py script runs pyTDDmon.pyw in "test mode" (flag --log-and-exit) in all
subdirectories of systest. In each directory, there is an "expected.log" file. That file
contains the correct output for pyTDDmon, for the directory in question. run_all.py
checks each and every expected.log, and compares with the newly created pytddmon.pyw.
For each broken exception, an informative message is printed to stdout.