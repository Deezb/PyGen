# PyGen
##Generate unit tests for Python 3.5.2  
### this is version 0.0.2, Creates Unit Tests, works with functions, conditionals and assignments over rational domains.
#### this version works with simple parameters, but does work with loops, lists, dicts, sets, tuples or comprehensions.
#### This code is part of a final yr college project to investigate the automatic generation of unit test data sets for Python.

###When the module pyGen.py is run it requests a filename to analyse using the easygui open file dialogue. 
### The user selects a .py module to analyse.
####The file is parsed using the ast module.
#### Paths through the code are identified.
#### Symbolic Execution is used to produce constraints for each path, the constraints are searched for satisfiability using a constraint solver.
#### (This version finds every path through a function and checks each one for satisfiability)
It is proposed in future versions to check each stage moving down through the execution paths for satisfiability to reduce path explosion by pruning unsatisfiable branches, reducing time and memory wasted creating paths for impossible branches.

####This version writes a module of unit tests which contains all of the unit tests for a selected module. 
The file of unit tests is currently placed in a folder in the same directory as the parent folder of the file being tested. 
so for a structure  /dir1/dir2/file1.py being tested creates the folder 
                    /dir1/pygen_unit_test/test_file1.py
This version produces a unit test for each satisfiable path that it finds using a class which inherits the unittest.Testcase class.
The tests are based on the assertEqual test method. When a path is found to have a satisfiable set of inputs, a set of input data is generated.  The input data is used to calculate the expected result based on Symbolic Execution and then sent as arguments to the function to check that the values returned are the same.
It will be then the job of a programmer or validator to see that the allowable type of inputs should produce the given output values.

In one of the first tests the input results was a rational 10.03 for a factorial function, factorials should only take integer values so this input set was an invalid answer, but only as the code allowed rational value to be entered, the code needed to check that the arguments are integers and this showed that the code was incomplete.

#### Their are a number of requirements to go with this package.
This package has only been built successfully on a windows computer, the author wasn't able to get the ECLiPSe package to work with other OSes, due to the complexity of requirements it is intended to create a docker image to abstract the configuration of the system for users.

### ECLiPSe clp needs to be downloaded and installed,  I installed it at "C:\ECLPS61"
### set ECLIPSEDIR=<wherever eclipse was installed, I used "set ECLIPSEDIR=C:\ECLPS61">
### set ARCH to suit your OS "set ARCH=i386_nt"
### add to path C:\ECLPS61\lib\i386_nt\
### set PATH=%PATH%;C:\ECLPS61\lib\i386_nt\

Install Python 3.5.2
packages used includes

####sympy             - for reducing symbolic formaulae
####easygui           - to select files
####ast_decompiler    - to rebuild the source code represented by a node

