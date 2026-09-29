---
name: notes-results
description: "Background notes about results in this environment. Version control keeps a history of changes. The current state of the files can be compared with earlier states. The history can show who changed a file, when it was changed and what the change was...."
---

## The shell

The shell runs commands. A command has a name and arguments. When a command finishes, it returns an
exit code. An exit code of zero usually means that the command succeeded. Other exit codes usually
mean that something did not work as expected. Commands can print text to standard output and to
standard error. Both kinds of output appear in the tool result.

Some commands finish quickly and some take longer. Long-running commands may be stopped by a time
limit. Commands can read environment variables. Environment variables are set for the process and
the processes it starts. The current directory of the shell can change when a command changes it.

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
can download files, call remote services and install packages from remote sources. When it is not
available, such operations fail with an error.

## Results

The outcome of the session is the state of the environment when the session ends, together with
anything the agent writes in its final message. The task description says what outcome is wanted.

## Glossary

**Argument.** A value passed to a command, a function or a program when it starts.

**Binary.** A file that contains machine code or other non-text data. Also used for an executable
program.

**Build.** The process of turning source files into a form that can be run, such as an executable,
a library or a package.

**Cache.** Stored data kept so that later requests for the same data are answered faster.

**Command line.** A text interface where commands are typed and their output is shown.

**Compiler.** A program that translates source code into another form, usually machine code or
bytecode.

**Configuration.** Settings that control how a program behaves. Configuration is often stored in
files or environment variables.

**Container.** An isolated environment that has its own file system and processes but shares the
kernel of the host machine.

**Dependency.** A package, library or program that another piece of software needs in order to
work.

**Directory.** A container for files and other directories in a file system. Also called a
folder.

**Environment variable.** A named value available to a process and inherited by the processes it
starts.

**Exception.** An event that interrupts the normal flow of a program, usually because of an      
