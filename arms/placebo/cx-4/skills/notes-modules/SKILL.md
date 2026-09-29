---
name: notes-modules
description: "Background notes about modules in this environment. The installed programs can be listed and their versions can be printed with the usual commands. Packages for a programming language are usually installed through that language's package manager......."
---

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
provides. Each tool call produces a result, and the result appears in the   
