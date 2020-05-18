[![Build Status](https://travis-ci.com/malcolmraine/PyFile.svg?branch=master)](https://travis-ci.com/malcolmraine/PyFile)

# PyFile
A file object wrapper for Python. This combines many file I/O and manipulation functions and properties into a single object. 
This package wraps up the functionality from the builtin pathlib and file handling functions. 

## Features
* MD5 and SHA256 file hashes as attributes
* General file attributes:
  * File modified status
  * Size
  * Base name
  * Dir name
  * File name
  
* Integrated Linux/Unix bash functionality:
  * grep
  * touch
* File backup creation
  * A single function creates a zip backup with an included SHA256 hash 

## Future Plans
* Encryption at rest