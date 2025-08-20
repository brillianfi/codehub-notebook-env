import logging
import shlex
import subprocess

import click


logger = logging.getLogger(__name__)


def call_as_root(command):
    logger.debug("Running command 'sudo sudocds {command}'")
    subprocess.call(shlex.split(f"sudo sudocds {command}"))


@click.group()
def cli():
    """Simple program that automates nbgrader stuff.

    \b
    The order of assignment commands should be:
    1. init (to create course)
    2. assignment generate (to generate created assignment)
    3. assignment release (release student version of assignment)
    4. assignment distribute (distribute assignment to students)
    5. assignment collect (collect assignments submitted by students)
    6. assignment autograde (autograde collected assignments)
    7. assignment feedback (generate and distribute assignment feedback to students)

    \b
    Additionally,
    - send can be used to copy a file or directory to other users
    - assignment generalstats can be used to get some statistics about an assignment
        (attempts, submits, average grade etc...)
    - assignment csvstats can be used to output student statistics to csv files (attempts,
        submits, grades etc...)
    - assignment remove can be used to remove an assignment from the gradebook, for example
        to allow a new version of the assignment to be released
    """


@cli.group()
def assignment():
    """Commands to manage assignments."""


@cli.command()
def init():
    call_as_root("init")


@cli.command()
@click.argument("path")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[],
    help=(
        "User to send file or directory PATH to. Can be specified multiple times"
        " to share with multiple users. Defaults to all users (students and"
        " admins) if none are given."
    ),
)
def send(path, user_list):
    """PATH: Relative path to file or directory.

    Copies the file or directory specified to other users. Retains directory
    hierarchy so that e.g. "cds send exampledir/examplefile.txt" will create
    the directory exampledir in the other users' home directories and copy
    examplefile.txt into it.
    """
    if user_list:
        users = " -u " + " -u ".join([user.lower() for user in user_list])
        call_as_root(f"send {path}" + users)
    else:
        call_as_root(f"send {path}")


# Assignment subcommands
@assignment.command()
@click.argument("assignment-name")
def generate(assignment_name):
    """ASSIGNMENT: assignment directory name.

    Generates the student version of ASSIGNMENT.
    """
    call_as_root(f"assignment generate {assignment_name}")


@assignment.command()
@click.argument("assignment-name")
def release(assignment_name):
    """ASSIGNMENT: assignment directory name.

    Prepares the student version of ASSIGNMENT to be distributed to students.
    """
    call_as_root(f"assignment release {assignment_name}")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[],
    help=(
        "Username of student to distribute ASSIGNMENT to. Can be specified multiple times to "
        "distribute to multiple students. Defaults to all students if none are given."
    ),
)
def distribute(assignment_name, user_list):
    """ASSIGNMENT: assignment directory name.

    Distributes the student version of ASSIGNMENT to students.
    """
    if user_list:
        users = " -u " + " -u ".join([user.lower() for user in user_list])
        call_as_root(f"assignment distribute {assignment_name}" + users)
    else:
        call_as_root(f"assignment distribute {assignment_name}")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[],
    help=(
        "Username of student to collect ASSIGNMENT from. Can be specified multiple times to "
        "collect from multiple students. Defaults to all students if none are given."
    ),
)
def collect(assignment_name, user_list):
    """ASSIGNMENT: assignment directory name.

    Collects submitted ASSIGNMENT from students.
    """
    if user_list:
        users = " -u " + " -u ".join([user.lower() for user in user_list])
        call_as_root(f"assignment collect {assignment_name}" + users)
    else:
        call_as_root(f"assignment collect {assignment_name}")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[],
    help=(
        "Username of student to autograde ASSIGNMENT for. Can be specified multiple times to "
        "autograde for multiple students. Defaults to all students if none are given."
    ),
)
def autograde(assignment_name, user_list):
    """ASSIGNMENT: assignment directory name.

    Autogrades collected ASSIGNMENT.
    """
    if user_list:
        users = " -u " + " -u ".join([user.lower() for user in user_list])
        call_as_root(f"assignment autograde {assignment_name}" + users)
    else:
        call_as_root(f"assignment autograde {assignment_name}")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[],
    help=(
        "Username of student to prepare feedback on ASSIGNMENT to. Can be specified multiple "
        "times to generate feedback for multiple students. Defaults to all students if none are "
        "given."
    ),
)
def feedback(assignment_name, user_list):
    """ASSIGNMENT: assignment directory name.

    Generates feedback on ASSIGNMENT for students.
    """
    if user_list:
        users = " -u " + " -u ".join([user.lower() for user in user_list])
        call_as_root(f"assignment feedback {assignment_name}" + users)
    else:
        call_as_root(f"assignment feedback {assignment_name}")


@assignment.command()
@click.argument("assignment-name")
def generalstats(assignment_name):
    """ASSIGNMENT: assignment directory name.

    Generates statistics about ASSIGNMENT
    """
    call_as_root(f"assignment generalstats {assignment_name}")


@assignment.command()
@click.argument("assignment-name", required=False)
def csvstats(assignment_name):
    """ASSIGNMENT: assignment directory name.

    Generates stats about ASSIGNMENT and saves it in csv format.
    If ASSIGNMENT is not specified it generates statistics for all assignments.
    """
    if assignment is True:
        call_as_root(f"assignment csvstats {assignment_name}")
    else:
        call_as_root("assignment csvstats")


@assignment.command()
@click.argument("assignment-name")
def remove(assignment_name):
    """ASSIGNMENT: assignment to remove.

    Removes ASSIGNMENT from the gradebook database.
    Does not remove any of the assignment files.
    """
    call_as_root(f"assignment remove {assignment_name}")


def main():
    cli()


if __name__ == "__main__":
    main()
