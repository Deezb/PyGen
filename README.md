# PyGen
##Generate unit tests for Python 3.5.2  
### version 0.0.2 Creates Unit Tests, works with functions, conditionals and assignments over rational domains.
####this version uses simple parameters, does not include loops, lists, dicts, sets, tuples, comprehensions.
#### This code is part of a college project to investigate the automatic generation of unit test data sets for Python.

#### The work uses Symbolic Execution of code to produce constraints and resolving the constraints using a constraint solver.
#### This version finds every path through a function and checks each one for satisfiability. 
It writes a module of unit tests which contains all of the unit tests for a selected module. 
The file of unit tests is currently placed in a folder in the same directory as the parent folder of the file being tested. 
so for a structure  /dir1/dir2/file1.py being tested creates the folder 
                    /dir1/pygen_unit_test/test_file1.py
It produces a unit test for each satisfiable path that it finds inheriting the unittest.Testcase class and self.assertEqual to compare the result expected from Symbolic execution to the result returned from calling the function with the constraint input variables found by consteaint satisfaction.

#### Their are a number of requirements to go with this package.
This package has only been built successfully on a windows computer, the author wasn't able to get the ECLiPSe package to work with other OSes, due to the complexity of requirements it is intended to create a docker image to abstract the configuration of the system for users.

### ECLiPSe clp needs to be downloaded and installed,  I installed it at "C:\ECLPS61"
### set ECLIPSEDIR=<wherever eclipse was installed, I used "set ECLIPSEDIR=C:\ECLPS61">
### set ARCH to suit your OS "set ARCH=i386_nt"
### add to path C:\ECLPS61\lib\i386_nt\
### set PATH=%PATH%;C:\ECLPS61\lib\i386_nt\

Install Python 3.5.2
packages used includes

sympy             - for reducing symbolic formaulae
easygui           - to select files
ast_decompiler    - to rebuild the source code represented by a node

