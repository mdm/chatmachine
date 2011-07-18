A Z-machine interpreter written in Python.
------------------------------------------

Goals:
  * Be fast enough to run Inform 7 games
  * A debugger
  * Interfaces for console, Faceboob Chat and Skype
  * Correctness

Current features:
  * JIT-compilation to Python bytecode
  * Caches blocks of code to avoid unneccessary recompilaton
  * Unit tests for all implemented operators
  * Runs version 1 games (i.e. Zork I, Release 5)

