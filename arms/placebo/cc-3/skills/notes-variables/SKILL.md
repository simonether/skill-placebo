---
name: notes-variables
description: "Background notes about variables in this environment. They are provided for reference only. A session starts with a message that describes a task. The message is written in plain language. It may mention files,............."
---

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

These notes describe the working environment of this session. They restate what the agent already
knows from its own instructions and add nothing new. They are provided for reference only.

## The session

A session starts with a message that describes a task. The message is written in plain language.
It may mention files, directories, commands, error messages, expected outputs or other details.
The task description is the main source of information about what is wanted. The session ends when
the agent stops working on the task.

The agent works inside a computer environment. The environment has a file system, a shell and a set
of installed programs. The agent interacts with the environment through the tools that the harness
provides. Each tool call produces a result, and the result appears in the conversation. The agent
reads the results and decides what to do next.

## The working directory

The session has a working directory. Relative paths are resolved against it. The working
directory usually contains the files that the task refers to. It may contain source code,
configuration files, data files, documentation, build scripts or other material. Some files may be
large and some may be small. Some directories may be deeply nested.

The contents of files can be read with the file tools or with shell commands. Files can be created,
changed or removed. Changes to files take effect immediately and remain for the rest of the
session.

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
be   
