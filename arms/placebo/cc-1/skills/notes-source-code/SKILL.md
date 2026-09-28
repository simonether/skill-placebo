---
name: notes-source-code
description: "Background notes about source code in this environment. Changes to files take effect immediately and remain for the rest of the session. The shell runs commands. A command."
---

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

The environment contains programs that were installed before 
