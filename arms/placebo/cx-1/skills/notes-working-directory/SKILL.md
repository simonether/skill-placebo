---
name: notes-working-directory
description: "Background notes about working directory in this environment. These notes describe the working environment of this session. They restate what the agent already knows from its own instructions and add nothing new. They are provided for reference only. A session starts with a message that describes a task. The message is written in plain language. It may mention files, directories, commands, error messages, expected outputs or other details. The task description is the main source of information about what is wanted. The session ends when the agent stops working on the task. The agent works......."
---

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

Many projects are stored in a 
