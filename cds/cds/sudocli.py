import logging
import os
import subprocess
import shutil
import sys
import datetime as dt

from distutils.dir_util import copy_tree
import click

from nbgrader.apps import NbGraderAPI
from nbgrader.api import MissingEntry
from traitlets.config import Config

import pandas as pd

from cds.helpers import (
    get_admins,
    recursive_chown,
    file2users,
    dir2users,
    get_assignment_fetches,
    get_assignment_contents,
    get_assignment_attempts,
    get_assignment_submits,
    print_assignment_stats,
    get_assignment_statistics,
)

from cds.add_selftests import AddSelftestsPreprocessor
from cds.remove_selftests import RemoveSelftestsPreprocessor

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    if os.getuid() != 0:
        logger.critical("sudocds run without root privileges")
        logger.critical("Unable to continue")
        print("Please re-run with sudo privilege or the program will not work.")
        print("Exiting...")
        sys.exit()

    config = Config()
    course_name = "course"
    config.Exchange.course_id = course_name
    config.CourseDirectory.course_id = course_name
    
    config.GenerateAssignment.preprocessors = [
        AddSelftestsPreprocessor,
        'nbgrader.preprocessors.IncludeHeaderFooter',
        'nbgrader.preprocessors.ClearSolutions',
        'nbgrader.preprocessors.LockCells',
        'nbgrader.preprocessors.ComputeChecksums',
        'nbgrader.preprocessors.SaveCells',
        'nbgrader.preprocessors.CheckCellMetadata',
        'nbgrader.preprocessors.ClearOutput',
        'nbgrader.preprocessors.ClearHiddenTests',
        'nbgrader.preprocessors.ClearMarkScheme',
    ]
    config.Autograde.sanitize_preprocessors = [
        RemoveSelftestsPreprocessor,
        'nbgrader.preprocessors.ClearOutput',
        'nbgrader.preprocessors.DeduplicateIds',
        'nbgrader.preprocessors.OverwriteKernelspec',
        'nbgrader.preprocessors.OverwriteCells',
        'nbgrader.preprocessors.CheckCellMetadata'
    ]

    # Increase default timeout to avoid timeout when grading exercises with slow
    # cells. Adjust this number as needed.
    config.ExecutePreprocessor.timeout = 300

    # Need to add both custom config here and in student_nbgrader_config.py
    config.ClearSolutions.code_stub = {
        "python": "### START ANSWER HERE ###\n### END ANSWER HERE ###"
    }

    paths = {
        "home_dir": os.path.join(os.sep, "home", "jovyan"),
        "root_dir": os.path.join(os.sep, "efs", "home"),
        "exchange_root_admin": os.path.join(os.sep, "home", "jovyan", "exchange"),
        "exchange_root_student": os.path.join(os.sep, "home", "jovyan", ".exchange"),
        "current_admin_course_dir": None,
        "course_exchange_admin": os.path.join("exchange", course_name),
        "course_exchange_student": os.path.join(".exchange", course_name),
        "outbound_dir_admin": None,
        "outbound_dir_student": None,
        "current_admin_outbound": None,
        "admin_submitted_dir": None,
        "inbound_dir_admin": None,
        "inbound_dir_student": None,
        "admin_inbound": None,
        "admin_autograded_dir": None,
        "admin_feedback_dir": None,
        "stats_dir": None,
    }

    config.CourseDirectory.root = os.path.join(paths["home_dir"], course_name)
    config.Exchange.root = paths["exchange_root_admin"]
    api = NbGraderAPI(config=config)

    current_admin, admins = get_admins(
        os.path.join(os.sep, "admins.txt"),
        paths["root_dir"]
    )

    paths["current_admin_course_dir"] = os.path.join(
        paths["root_dir"], current_admin, course_name
    )
    paths["outbound_dir_admin"] = os.path.join(
        paths["course_exchange_admin"], "outbound"
    )
    paths["outbound_dir_student"] = os.path.join(
        paths["course_exchange_student"], "outbound"
    )
    paths["current_admin_outbound"] = os.path.join(
        paths["root_dir"], current_admin, paths["outbound_dir_admin"]
    )
    paths["inbound_dir_admin"] = os.path.join(paths["course_exchange_admin"], "inbound")
    paths["inbound_dir_student"] = os.path.join(
        paths["course_exchange_student"], "inbound"
    )
    paths["current_admin_inbound"] = os.path.join(
        paths["root_dir"], current_admin, paths["inbound_dir_admin"]
    )
    paths["admin_submitted_dir"] = os.path.join(
        paths["current_admin_course_dir"], "submitted"
    )
    paths["admin_autograded_dir"] = os.path.join(
        paths["current_admin_course_dir"], "autograded"
    )
    paths["admin_feedback_dir"] = os.path.join(
        paths["current_admin_course_dir"], "feedback"
    )
    paths["stats_dir"] = os.path.join(paths["home_dir"], "stats")

    def path_is_dir(user):
        return os.path.isdir(os.path.join(str(paths["root_dir"]), user))

    students = [
        user
        for user in os.listdir(paths["root_dir"])
        if user not in admins and path_is_dir(user)
    ]

    users = {
        "admins": admins,
        "students": students,
        "current_admin": current_admin,
    }

    ids = {"admin_uid": 1000, "admin_gid": 100, "root_id": 0}

    ctx.obj = dict(
        api=api,
        course_name=course_name,
        paths=paths,
        users=users,
        ids=ids,
    )

    logger.debug(f"Current admin: {current_admin}")
    logger.debug(f"Admins: {admins}")
    logger.debug(f"Students: {students}")
    logger.debug(f"Paths: {paths}")


@cli.group()
@click.pass_context
def assignment(ctx):
    ctx.obj["assignments"] = ctx.obj["api"].get_assignments()
    ctx.obj["released_assignments"] = ctx.obj["api"].get_released_assignments()
    logger.debug(f"Assignments: {ctx.obj['assignments']}")
    logger.debug(f"Released assignments: {ctx.obj['released_assignments']}")


@cli.command()
@click.pass_context
def init(ctx):
    logger.info("Running init")
    logger.info("Initializing course")
    print("Initializing course...")

    paths = ctx.obj["paths"]
    ids = ctx.obj["ids"]

    source_dir = os.path.join(paths["current_admin_course_dir"], "source")
    logger.debug(f"Creating assignment source dir: {source_dir}")
    os.makedirs(source_dir, exist_ok=True)

    logger.debug("chowning assignment source dir to admin")
    os.chown(paths["current_admin_course_dir"], ids["admin_uid"], ids["admin_gid"])
    recursive_chown(
        paths["current_admin_course_dir"], ids["admin_uid"], ids["admin_gid"]
    )

    logger.debug("chowning exchange dir")
    recursive_chown(paths["exchange_root_admin"], ids["admin_uid"], ids["admin_gid"])

    logger.info("Course initialized")
    print("Done!")


@cli.command()
@click.argument("path")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[]
)
@click.pass_context
def send(ctx, path, user_list):
    logger.info(f"Running send {path} to {user_list}")
    print(f"Copying {path}...")

    users = ctx.obj["users"].copy()
    current_admin = users["current_admin"]

    if not user_list:
        logger.info("Users not specified, setting all students and admins")
        user_list = users["students"] + users["admins"]

    logger.debug(f"user_list: {user_list}")

    paths = ctx.obj["paths"]
    ids = ctx.obj["ids"]

    abs_path = os.path.abspath(path)

    if os.path.commonpath([abs_path, paths["home_dir"]]) != paths["home_dir"]:
        logger.error(f"Path {abs_path} is not part of your home directory.")
        logger.error("Exiting")
        print(f"Path {abs_path} is not part of your home directory.")
        print("Exiting")
        sys.exit(1)

    safe_path = os.path.join(*abs_path.split("/")[3:])

    targets = [
        os.path.join(paths["root_dir"], user, safe_path)
        for user in user_list
        if user != current_admin
    ]

    if os.path.isfile(path):
        logger.debug("Running file2users with:")
        logger.debug(f"Source: {path}")
        logger.debug(f"Targets: {targets}")
        file2users(path, targets, ids["admin_uid"], ids["admin_gid"])

    if os.path.isdir(path):
        logger.debug("Running dir2users with:")
        logger.debug(f"Source: {path}")
        logger.debug(f"Targets: {targets}")
        dir2users(path, targets, ids["admin_uid"], ids["admin_gid"])

    logger.info("Finished running send")


@assignment.command()
@click.argument("assignment-name")
@click.pass_context
def generate(ctx, assignment_name):
    logger.info(f"Running generate on assignment {assignment_name}")
    print("Generating assignment...")

    api = ctx.obj["api"]
    paths = ctx.obj["paths"]
    ids = ctx.obj["ids"]

    source_dir = os.path.join(
        paths["current_admin_course_dir"], "source", assignment_name
    )
    logger.debug(f"source_dir: {source_dir}")
    release_dir = os.path.join(
        paths["current_admin_course_dir"], "release", assignment_name
    )
    logger.debug(f"release_dir: {release_dir}")

    if os.path.exists(source_dir):
        logger.debug(f"Directory {source_dir} exists.")
        logger.debug(f"chowning to root: {source_dir}")
        recursive_chown(source_dir, ids["root_id"], ids["root_id"])
        logger.debug(f"chowning to root: {release_dir}")
        recursive_chown(release_dir, ids["root_id"], ids["root_id"])

        notebooks = [
            os.path.join(source_dir, notebook)
            for notebook in os.listdir(source_dir)
            if notebook.endswith(".ipynb")
        ]
        logger.debug(f"notebooks: {notebooks}")

        for notebook in notebooks:
            logger.debug(f"Running nbgrader update {notebook}")
            subprocess.run(
                ["nbgrader", "update", notebook],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

        result = api.generate_assignment(assignment_name)
        logger.debug(f"result: {result}")

        logger.debug(f"chowning to admin: {source_dir}")
        recursive_chown(source_dir, ids["admin_uid"], ids["admin_gid"])
        logger.debug(f"chowning to admin: {release_dir}")
        recursive_chown(release_dir, ids["admin_uid"], ids["admin_gid"])

        if "error" in result:
            logger.error(f"Error generating assignment: {result['error']}")
            print("An error occurred while generating the assignment.")
        else:
            logger.info(f"Finished generating assignment {assignment_name}")
            print("Done!")
    else:
        logger.error(f"Path does not exist: {source_dir}")
        print(f"Assignment '{assignment_name}' doesn't exist in the source directory")
        print("Create the assignment first")


@assignment.command()
@click.argument("assignment-name")
@click.pass_context
def release(ctx, assignment_name):
    logger.info("Running release {assignment_name}")
    print("Releasing assignment...")

    api = ctx.obj["api"]
    current_admin_course_dir = ctx.obj["paths"]["current_admin_course_dir"]
    exchange_root_admin = ctx.obj["paths"]["exchange_root_admin"]
    root_id = ctx.obj["ids"]["root_id"]
    current_admin = ctx.obj["users"]["current_admin"]

    # Add current admin to gradebook
    logger.debug(f"Adding {current_admin} to the gradebook")
    gradebook = api.gradebook
    gradebook.update_or_create_student(current_admin)
    logger.debug("Closing gradebook")
    gradebook.close()

    assignment_dir = os.path.join(current_admin_course_dir, "release", assignment_name)
    logger.debug(f"assignment_dir: {assignment_dir}")

    if os.path.exists(assignment_dir):
        logger.debug(f"chowning {assignment_dir} to root")
        recursive_chown(assignment_dir, root_id, root_id)
        logger.debug(f"chowning {exchange_root_admin} to root")
        recursive_chown(exchange_root_admin, root_id, root_id)

        logger.debug("Unreleasing previous assignment")
        _ = api.unrelease(assignment_name)
        logger.debug("Releasing assignment {assignment_name}")
        result = api.release_assignment(assignment_name)
        logger.debug(f"result: {result}")

        if "error" in result:
            logger.error(f"Error releasing assignment: {result}")
            print("An error occurred while releasing the assignment.")
        else:
            logger.info(f"Finished releasing assignment {assignment_name}")
            print("Done!")
    else:
        logger.error(f"Path does not exist: {assignment_dir}")
        print(f"Assignment '{assignment_name}' doesn't exist in the release directory")
        print("Generate the assignment first")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[]
)
@click.pass_context
def distribute(ctx, assignment_name, user_list):
    logger.info(f"Running distribute {assignment_name}")
    print("Distributing assignments...")

    paths = ctx.obj["paths"]
    admin_uid = ctx.obj["ids"]["admin_uid"]
    admin_gid = ctx.obj["ids"]["admin_gid"]
    root_id = ctx.obj["ids"]["root_id"]
    users = ctx.obj["users"]


    if not user_list:
        logger.info("Users not specified, setting all students and admins")
        user_list = users["students"] + users["admins"]

    logger.debug(f"user_list: {user_list}")

    assignment_outbound = os.path.join(paths["current_admin_outbound"], assignment_name)
    logger.debug(f"assignment_outbound: {assignment_outbound}")
    if os.path.exists(assignment_outbound):
        logger.debug(f"chowning {assignment_outbound} to root")
        recursive_chown(assignment_outbound, root_id, root_id)

        def get_destination(user):
            if user in users["admins"]:
                logger.debug(f"User {user} is an admin")
                logger.debug(f"Using {paths['outbound_dir_admin']}")
                return os.path.join(
                    paths["root_dir"],
                    user,
                    paths["outbound_dir_admin"]
                )
            logger.debug(f"User {user} is a student")
            logger.debug(f"Using {paths['outbound_dir_student']}")
            return os.path.join(
                paths["root_dir"],
                user,
                paths["outbound_dir_student"]
            )

        destinations = map(lambda user: (get_destination(user), user), user_list)

        gradebook = ctx.obj["api"].gradebook

        for destination, user in destinations:
            if user != users["current_admin"]:

                logger.debug(f"Updating/creating {user} in gradebook")
                gradebook.update_or_create_student(user)

                user_assignment_dir = os.path.join(destination, assignment_name)
                logger.debug(f"user_assignment_dir: {user_assignment_dir}")

                if os.path.exists(user_assignment_dir):
                    logger.debug(f"{user_assignment_dir} already exists")
                    logger.debug("Removing dir before continuing")
                    shutil.rmtree(user_assignment_dir)

                logger.debug(f"Copying assignment to {user}.")
                copy_tree(
                    os.path.join(paths["current_admin_outbound"], assignment_name),
                    user_assignment_dir,
                )
                logger.debug(f"chowning {user_assignment_dir} to admin")
                recursive_chown(user_assignment_dir, admin_uid, admin_gid)

        logger.debug("Closing gradebook.")
        gradebook.close()
        logger.debug(f"chowning {assignment_outbound} to admin")
        recursive_chown(assignment_outbound, admin_uid, admin_gid)
        logger.info("Finished distributing assignment.")
        print("Done!")
    else:
        logger.error(f"Path does not exist: {assignment_outbound}")
        print(
            f"Assignment '{assignment_name}' doesn't exist in the outbound directory"
        )
        print("Release the assignment first")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[]
)
@click.pass_context
def collect(ctx, assignment_name, user_list):
    logger.info(f"Running collect {assignment_name}")
    print("Collecting assignments...")

    paths = ctx.obj["paths"]
    ids = ctx.obj["ids"]
    users = ctx.obj["users"]

    if not user_list:
        logger.info("Users not specified, setting all students and admins")
        user_list = users["students"] + users["admins"]

    logger.debug(f"user_list: {user_list}")

    if os.path.exists(paths["admin_submitted_dir"]):
        logger.debug(f"{paths['admin_submitted_dir']} exists")
        logger.debug(f"chowning {paths['admin_submitted_dir']} to root")
        recursive_chown(paths["admin_submitted_dir"], ids["root_id"], ids["root_id"])
    if os.path.exists(paths["current_admin_inbound"]):
        logger.debug(f"{paths['current_admin_inbound']} exists")
        logger.debug(f"chowning {paths['current_admin_inbound']} to root")
        recursive_chown(paths["current_admin_inbound"], ids["root_id"], ids["root_id"])

    def get_source(user):
        if user in users["admins"]:
            logger.debug(f"User {user} is an admin")
            logger.debug(f"Using {paths['inbound_dir_admin']}")
            return os.path.join(
                paths["root_dir"],
                user,
                paths["inbound_dir_admin"]
            )
        logger.debug(f"User {user} is a student")
        logger.debug(f"Using {paths['inbound_dir_student']}")
        return os.path.join(
            paths["root_dir"],
            user,
            paths["inbound_dir_student"]
        )

    for user in user_list:
        if user != users["current_admin"]:
            inbound_src = get_source(user)
            logger.debug(f"inbound_src: {inbound_src}")
            srcs = [
                os.path.join(inbound_src, x)
                for x in os.listdir(inbound_src)
                if assignment_name in x
            ]
            logger.debug(f"srcs: {srcs}")
            src_names = [
                x
                for x in os.listdir(inbound_src)
                if assignment_name in x
            ]
            logger.debug(f"src_names: {src_names}")

            for name, src in zip(src_names, srcs):
                logger.debug(
                    "Creating dir" +
                    f"{os.path.join(paths['current_admin_inbound'], name)}"
                )
                os.makedirs(
                    os.path.join(paths["current_admin_inbound"], name),
                    exist_ok=True
                )

                logger.debug("Retrieving submitted assignment")
                copy_tree(
                    src,
                    os.path.join(
                        paths["current_admin_inbound"],
                        name
                    )
                )

    logger.info(f"Collecting {assignment_name} with nbgrader api")
    result = ctx.obj["api"].collect(assignment_name)
    logger.debug(f"result: {result}")

    logger.debug(f"chowning {paths['admin_submitted_dir']} to admin")
    recursive_chown(paths["admin_submitted_dir"], ids["admin_uid"], ids["admin_gid"])
    logger.debug(f"chowning {paths['current_admin_inbound']} to admin")
    recursive_chown(paths["current_admin_inbound"], ids["admin_uid"], ids["admin_gid"])

    if "error" in result:
        logger.error(f"Error collecting assignment: {result['error']}")
        print("An error occurred while collecting assignment.")
    else:
        submitted = [
            user
            for user in user_list
            if os.path.exists(
                os.path.join(
                    paths["admin_submitted_dir"],
                    user,
                    assignment_name
                )
            )
        ]
        logger.debug(f"submitted: {submitted}")
        print(f"{len(submitted)}/{len(user_list)} submissions collected")

        logger.info("Finished collecting {assignment_name}")
        print("Done!")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[]
)
@click.pass_context
def autograde(ctx, assignment_name, user_list):
    logger.info(f"Running autograde {assignment_name}")
    print("Autograding assignments...")

    paths = ctx.obj["paths"]
    ids = ctx.obj["ids"]
    users = ctx.obj["users"]

    if not user_list:
        logger.info("Users not specified, setting all students and admins")
        user_list = users["students"] + users["admins"]

    logger.debug(f"user_list: {user_list}")

    admin_submitted_dir = os.path.join(paths["current_admin_course_dir"], "submitted")
    admin_autograded_dir = os.path.join(paths["current_admin_course_dir"], "autograded")

    if os.path.exists(admin_submitted_dir):
        logger.debug(f"chowning {admin_submitted_dir} to root")
        recursive_chown(admin_submitted_dir, ids["root_id"], ids["root_id"])
    if os.path.exists(admin_autograded_dir):
        logger.debug(f"chowning {admin_autograded_dir} to root")
        recursive_chown(admin_autograded_dir, ids["root_id"], ids["root_id"])

    for user in user_list:
        user_autograded_dir = os.path.join(
            admin_autograded_dir, user, assignment_name
        )
        if os.path.exists(user_autograded_dir):
            logger.debug(f"{user_autograded_dir} already exists")
            logger.debug("Removing dir before continuing")
            shutil.rmtree(user_autograded_dir)

        print(f"Grading user {user} for assignment {assignment_name}")

        submitted_assignment_path = os.path.join(
            admin_submitted_dir, user, assignment_name
        )
        if os.path.exists(submitted_assignment_path):
            notebooks = [
                os.path.join(submitted_assignment_path, notebook)
                for notebook in os.listdir(submitted_assignment_path)
                if notebook.endswith(".ipynb")
            ]
            logger.debug(f"notebooks: {notebooks}")

            for notebook in notebooks:
                if os.path.exists(notebook):
                    logger.info(f"Running nbgrader update {notebook}")
                    subprocess.run(
                        ["nbgrader", "update", notebook],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )

            result = ctx.obj["api"].autograde(assignment_name, user, force=True)
            logger.debug(f"Result: {result}")
            if "error" in result:
                logger.error(f"Error grading assignment: {result['error']}")
                print("An error occurred during grading.")

    logger.debug(f"chowning {admin_submitted_dir} to admin")
    recursive_chown(admin_submitted_dir, ids["admin_uid"], ids["admin_gid"])
    logger.debug(f"chowning {admin_autograded_dir} to admin")
    recursive_chown(admin_autograded_dir, ids["admin_uid"], ids["admin_gid"])

    autograded = [
        user
        for user in user_list
        if os.path.exists(os.path.join(admin_autograded_dir, user, assignment_name))
    ]

    logger.debug(f"autograded: {autograded}")
    print(f"{len(autograded)}/{len(user_list)} assignments autograded")

    logger.info(f"Finished autograding {assignment_name}")
    print("Done!")


@assignment.command()
@click.argument("assignment-name")
@click.option(
    "--user",
    "-u",
    "user_list",
    required=False,
    multiple=True,
    default=[]
)
@click.pass_context
def feedback(ctx, assignment_name, user_list):
    logger.info(f"Running feedback {assignment_name}")
    print("Generating assignment feedback...")

    paths = ctx.obj["paths"]
    ids = ctx.obj["ids"]
    users = ctx.obj["users"]

    if not user_list:
        logger.info("Users not specified, setting all students and admins")
        user_list = users["students"] + users["admins"]

    logger.debug(f"user_list: {user_list}")

    if os.path.exists(paths["admin_feedback_dir"]):
        logger.debug(f"chowning {paths['admin_feedback_dir']} to root")
        recursive_chown(paths["admin_feedback_dir"], ids["root_id"], ids["root_id"])
    if os.path.exists(paths["admin_autograded_dir"]):
        logger.debug(f"chowning {paths['admin_autograded_dir']} to root")
        recursive_chown(paths["admin_autograded_dir"], ids["root_id"], ids["root_id"])

        for user in user_list:
            destination = os.path.join(paths["root_dir"], user, "feedback")
            user_feedback_dir = os.path.join(paths["admin_feedback_dir"], user)

            if os.path.exists(os.path.join(user_feedback_dir, assignment_name)):
                logger.debug(f"{user_feedback_dir} already exists")
                logger.debug("Removing dir before continuing")
                shutil.rmtree(os.path.join(user_feedback_dir, assignment_name))

            if os.path.exists(
                os.path.join(paths["admin_autograded_dir"], user, assignment_name)
            ):
                logger.info(f"Generating feedback for {user}")
                result = ctx.obj["api"].generate_feedback(assignment_name, student_id=user)
                logger.debug(f"result: {result}")

                if "error" in result:
                    logger.error(f"Error creating feedback: {result['error']}")
                    print("An error occurred while generating feedback")

                if os.path.exists(user_feedback_dir):
                    logger.debug(f"Copying feedback to {user_feedback_dir}")
                    copy_tree(user_feedback_dir, destination)

        logger.debug(f"chowning {paths['admin_autograded_dir']} to admin")
        recursive_chown(
            paths["admin_autograded_dir"], ids["admin_uid"], ids["admin_gid"]
        )
        logger.debug(f"chowning {paths['admin_feedback_dir']} to admin")
        recursive_chown(
            paths["admin_feedback_dir"], ids["admin_uid"], ids["admin_gid"]
        )

        feedbacked = [
            user
            for user in user_list
            if os.path.exists(
                os.path.join(paths["admin_feedback_dir"], user, assignment_name)
            )
        ]
        logger.debug(f"Feedbacked: {feedbacked}")
        print(
            f"Generated assignment feedback for {len(feedbacked)}/{len(user_list)} users"
        )

        logger.info(f"Finished distributing feedback for {assignment_name}")
        print("Done!")
    else:
        logger.error(f"Path does not exist: {paths['admin_autograded_dir']}")
        print("Autograded directory doesn't exist in the outbound directory")
        print("Release the assignment first")


@assignment.command()
@click.argument("assignment-name")
@click.pass_context
def generalstats(ctx, assignment_name):
    logger.info(f"Running generalstats {assignment_name}")
    print("Generating general student assignment stats...")
    api = ctx.obj["api"]
    paths = ctx.obj["paths"]
    students = ctx.obj["users"]["students"]

    fetched_students = get_assignment_fetches(
        paths["root_dir"], assignment_name, students
    )
    logger.debug(f"fetched_students: {fetched_students}")
    assignment_contents = get_assignment_contents(
        paths["current_admin_outbound"], assignment_name
    )
    logger.debug(f"assignment_contents: {assignment_contents}")
    attempts = get_assignment_attempts(
        fetched_students,
        paths["root_dir"],
        assignment_name,
        paths["current_admin_outbound"],
    )
    logger.debug(f"attempts: {attempts}")
    notebooks = [
        f[:-6]
        for f in os.listdir(assignment_contents["assignment_path"])
        if ".ipynb" in f
    ]
    logger.debug(f"notebooks: {notebooks}")

    total_submits, collected_submits, uncollected_submits = get_assignment_submits(
        students,
        paths["home_dir"],
        assignment_name,
        paths["root_dir"],
        paths["course_exchange_student"],
    )
    logger.debug(f"total_submits: {total_submits}")
    logger.debug(f"collected_submits: {collected_submits}")
    logger.debug(f"uncollected_submits: {uncollected_submits}")

    assignment_stats = {
        "fetched_students": fetched_students,
        "students": students,
        "assignment_name": assignment_name,
        "notebooks": notebooks,
        "attempts": attempts,
        "total_submits": total_submits,
        "uncollected_submits": uncollected_submits,
        "collected_submits": collected_submits,
    }
    logger.debug(f"Assignment stats: {assignment_stats}")

    logger.info("Printing assignment statistics")
    print_assignment_stats(assignment_stats, api)
    logger.info("Finished generating generalstats")


@assignment.command()
@click.argument("assignment-name", required=False)
@click.pass_context
def csvstats(ctx, assignment_name):
    logger.info(f"Running csvstats {assignment_name}")
    api = ctx.obj["api"]
    paths = ctx.obj["paths"]
    students = ctx.obj["users"]["students"]

    if assignment_name:
        assignments = set([assignment_name])
        logger.debug(f"Assignments: {assignments}")
    else:
        logger.info("Assignment not specified, setting all assignments")
        assignments = ctx.obj["released_assignments"]
        logger.debug(f"assignments: {assignments}")

    assignment_scores = {}

    logger.debug(f"mkdir {paths['stats_dir']}")
    os.makedirs(paths["stats_dir"], exist_ok=True)

    local_time = dt.datetime.now().isoformat()

    for released_assignment in assignments:
        assignment_key, assignment_statistics = get_assignment_statistics(
            api, paths, students, released_assignment, local_time
        )
        logger.debug(f"assignment_key: {assignment_key}")
        logger.debug(f"assignment_statistics: {assignment_statistics}")

        assignment_scores[assignment_key] = {
            student: assignment_statistics[student][assignment_key]
            for student in students
        }
        logger.debug(f"assignment_scores: {assignment_scores}")

    assignment_scores_df = pd.DataFrame.from_dict(assignment_scores).astype(float)
    assignment_scores_df["total_score"] = assignment_scores_df.sum(axis=1)
    assignment_scores_df["student"] = assignment_scores_df.index
    logger.debug(f"assignment_scores_df: {assignment_scores_df}")
    logger.info("Writing stats to .csv")
    assignment_scores_df.to_csv(
        f"{os.path.join(paths['stats_dir'], 'summary')}_{local_time}.csv", index=False
    )
    logger.info("Finished generating csvstats")


@assignment.command()
@click.argument("assignment-name")
@click.pass_context
def remove(ctx, assignment_name):
    logger.info(f"Running remove {assignment_name}")
    gradebook = ctx.obj["api"].gradebook

    try:
        logger.info(f"Removing assignment {assignment_name}...")
        gradebook.remove_assignment(assignment_name)
        logger.info(f"Removed assignment {assignment_name}!")
        print("Assignment successfully removed")
    except MissingEntry:
        logger.exception(f"Error: Assignment {assignment_name} does not exist!")
    finally:
        logger.debug("Closing gradebook")
        gradebook.close()

    logger.info("Finished removing assignment")


def main():
    # pylint: disable=no-value-for-parameter, unexpected-keyword-arg
    cli(obj={})


if __name__ == "__main__":
    main()
