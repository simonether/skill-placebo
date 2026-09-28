---
name: notes-permissions
description: "Background notes about permissions in this environment. The environment has a file system, a shell and a set of installed programs. The agent........"
---

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

**Exception.** An event that interrupts the normal flow of a program, usually because of an error.

**Exit code.** A number returned by a process when it finishes. Zero usually means success.

**File system.** The structure that stores files and directories on a disk or in memory.

**Function.** A named block of code that can be called with arguments and may return a value.

**Interpreter.** A program that runs source code directly, without a separate compilation step.

**Library.** A collection of code that other programs can use.

**Log.** A record of events written by a program while it runs.

**Module.** A file or unit of code that groups related definitions.

**Package manager.** A program that installs, updates and removes packages and their
dependencies.

**Path.** The location of a file or directory, written as a sequence of directory names.

**Permission.** A rule that says which users or processes may read, write or run a file.

**Process.** A running instance of a program.

**Repository.** A storage location for a project's files and their history.

**Script.** A file containing commands or code that is run by an interpreter.

**Standard error.** An output stream where programs usually write error messages.

**Standard input.** An input stream from which programs can read data.

**Standard output.** An output stream where programs usually write their normal output.

**Symbolic link.** A file that points to another file or directory.

**Timeout.** A limit on how long an operation may run before it is stopped.

**Variable.** A named location that holds a value in a program.

**Version.** An identifier that distinguishes one release of software from another.

**Virtual environment.** An isolated set of installed packages for a programming language.

These notes describe the working environment of this session. They restate what the agent 
