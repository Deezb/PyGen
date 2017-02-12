# PyGen
##Generate unit tests for Python 3.5.2  

This code is part of a college project to investigate the automatic generation of unit test data sets for Python.

The work is based on symbolic execution of code to produce constraints and resolving the constraints using a constraint solver.














Their are a number of requirements to go with this package.











This package has only been built on a windows computer, the ECLiPSe package hasn't been updated to work with other OSes

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

