---
name: notes-configuration
description: "Background notes about configuration in this environment. **Cache.** Stored data kept so that later requests for the same data are answered...."
---

## Programs and packages

The environment contains programs that were installed before the session began. Programming
language interpreters, compilers, package managers and command-line utilities may be present.
Which versions are installed depends on the environment. The installed programs can be listed
and their versions can be printed with the usual commands.

Packages for a programming language are usually installed through that language's package manager.
Installed packages are available to programs that use the same interpreter or environment.
Some environments use virtual environments or containers to keep packages separate.

## Source code

Source code is organised into files and directories. A project may use one programming language or
several. Code in one file can refer to code in another file. Projects often include a configuration
file that names the project, lists its dependencies and describes how it is built or run.

Projects may contain automated checks such as unit tests, integration tests, linters or type
checkers. These checks are programs that report whether some property of the code holds. Their
results appear as output when they run.

## Version control

Many projects are stored in a version control system. Version control keeps a history of changes.
The current state of the files can be compared with earlier states. The history can show who
changed a file, when it was changed and what the change was. The working directory may or may not
be part of a repository.

## Text and data formats

Files come in many formats. Plain text files contain characters arranged in lines. Structured
formats such as JSON, YAML, TOML, CSV and XML follow rules about how data is written. Binary files
contain bytes that are not meant to be read as text. Tools exist for reading and writing each
format.

Line endings, character encodings and trailing whitespace are properties of text files. Different
systems use different conventions for them. A file keeps the conventions it was written with unless
something changes them.

## Networks

Some environments have network access and some do not. When network access is available, programs
can download files, call remote  
