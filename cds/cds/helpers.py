import logging
import os
import shutil
import socket
import sys
from urllib.parse import unquote
from nbgrader.api import MissingEntry

import pandas as pd


logger = logging.getLogger(__name__)


def get_admins(filepath, root_dir):
    with open(filepath, errors="replace") as f:
        content = f.readline()

    admins = [
        admin
        for admin in content.rstrip().split(" ")
        if os.path.isdir(os.path.join(root_dir, admin))
    ]
    hostname = str(socket.gethostname())[8:]

    # Decoding the z2jh encoded usernames
    current_admin = unquote(hostname.replace("-", "%"))

    if current_admin not in admins:
        logger.critical(f"User {current_admin} not in {admins}, exiting.")
        print(f"WARNING! current user {current_admin} is not an admin user")
        print("Exiting...")
        sys.exit()

    return current_admin, admins


def recursive_chown(root_dir, uid, gid):
    gradebook = os.path.join(os.sep, "home", "jovyan", "course", "gradebook.db")
    if os.path.exists(gradebook):
        os.chown(gradebook, uid, gid)
    for root, dirs, files in os.walk(root_dir):
        for d in dirs:
            os.chown(os.path.join(root, d), uid, gid)
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)


def _read_file(filepath):
    try:
        with open(filepath, "r", errors="replace") as f:
            content = f.readlines()
        return content
    except FileNotFoundError:
        logger.exception(f"{filepath} does not exist")
        return None


def file2users(filepath, target_files, admin_uid=1000, admin_gid=100):
    if not os.path.isfile(filepath):
        logger.error(f"{filepath} does not exist")
        sys.exit()

    for target_file in target_files:
        if not os.path.isdir(os.path.dirname(target_file)):
            logger.info(f"Target {target_file} dir doesn't exist, creating.")
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
        logger.info(f"Copying {filepath} to {target_file}")
        shutil.copy(filepath, target_file)
        recursive_chown(target_file, admin_uid, admin_gid)

    logger.info(f"Copied {filepath} to {len(target_files)} users")


def dir2users(src_dir, target_dirs, admin_uid=1000, admin_gid=100):
    if not os.path.isdir(src_dir):
        logger.info("Directory does not exist, creating")
        os.makedirs(src_dir, exist_ok=True)
    for target_dir in target_dirs:
        logger.info(f"Copying {src_dir} to {target_dir}")
        shutil.copytree(src_dir, target_dir, dirs_exist_ok=True)
        recursive_chown(target_dir, admin_uid, admin_gid)

    logger.info(f"Copied {src_dir} to {len(target_dirs)} users")


def student_fetched(root_dir, assignment, student):
    return os.path.isdir(os.path.join(root_dir, student, assignment))


def get_assignment_fetches(root_dir, assignment, students):
    return [
        student
        for student in students
        if student_fetched(root_dir, assignment, student)
    ]


def get_assignment_contents(current_admin_outbound, assignment):
    assignment_path = os.path.join(current_admin_outbound, assignment)
    assignment_files = [f for f in os.listdir(assignment_path) if ".ipynb" in f]
    original_contents = {
        filepath: _read_file(os.path.join(assignment_path, filepath))
        for filepath in assignment_files
    }

    contents = {
        "assignment_path": assignment_path,
        "assignment_files": assignment_files,
        "original_contents": original_contents,
    }
    return contents  # assignment_path, assignment_files, original_contents


def student_attempted(student, root_dir, assignment, current_admin_outbound):
    student_path = os.path.join(root_dir, student, assignment)
    if not os.path.isdir(student_path):
        return False

    assignment_contents = get_assignment_contents(current_admin_outbound, assignment)

    new_contents = {
        filepath: _read_file(os.path.join(student_path, filepath))
        for filepath in assignment_contents["assignment_files"]
    }
    for oc_file in assignment_contents["original_contents"]:
        if assignment_contents["original_contents"][oc_file] != new_contents[oc_file]:
            return True  # student has made an attempt
    return False


def get_assignment_attempts(students, root_dir, assignment, current_admin_outbound):
    return sum(
        1
        for student in students
        if student_attempted(student, root_dir, assignment, current_admin_outbound)
    )


def student_submitted(student, home_dir, assignment, root_dir, course_exchange_student):
    student_assignment_dir = os.path.join(
        home_dir, "course", "submitted", student, assignment
    )
    if os.path.isdir(student_assignment_dir):
        return True, "collected"

    inbound_dir = os.path.join(root_dir, student, course_exchange_student, "inbound")
    files = os.listdir(inbound_dir)
    for f in files:
        if assignment in f:
            return True, "uncollected"
    return False, None


def get_assignment_submits(
    students, home_dir, assignment, root_dir, course_exchange_student
):
    submits = [
        student_submitted(
            student, home_dir, assignment, root_dir, course_exchange_student
        )
        for student in students
    ]
    total_submits = [submit[1] for submit in submits if submit[0] is True]
    collected_submits = [submit for submit in total_submits if submit == "collected"]
    uncollected_submits = [
        submit for submit in total_submits if submit == "uncollected"
    ]

    return len(total_submits), len(collected_submits), len(uncollected_submits)


def get_student_assignment_scores(api, student, assignment):
    try:
        notebook_scores = {
            notebook.name: f"{notebook.score:.2f}"
            for notebook in api.gradebook.find_submission(assignment, student).notebooks
        }

        return {
            "assignment_score": f"{api.gradebook.find_submission(assignment, student).score:.2f}",
            "notebook_scores": notebook_scores,
        }
    except MissingEntry:
        logger.info(f"{student} didn't submit {assignment}")
        return {"assignment_score": 0, "notebook_scores": {}}


def print_assignment_stats(assignment_stats, api):
    print(
        f"\n{len(assignment_stats['fetched_students'])}/{len(assignment_stats['students'])} "
        f"students have fetched the assignment \"{assignment_stats['assignment_name']}\""
    )
    print(
        f"{assignment_stats['attempts']}/{len(assignment_stats['students'])} students have "
        f"attempted the assignment \"{assignment_stats['assignment_name']}\""
    )

    print(
        f"{assignment_stats['total_submits']}/{len(assignment_stats['students'])} students "
        f"have submitted the assignment \"{assignment_stats['assignment_name']}\""
    )
    if assignment_stats["uncollected_submits"] > assignment_stats["collected_submits"]:
        print(
            f"{assignment_stats['uncollected_submits']} of which have not been collected"
        )
        print(
            f"Run `cds collect \"{assignment_stats['assignment_name']}\"` to collect it"
        )

    nb_max_scores = {
        notebook["name"]: f"{notebook['max_score']:.2f}"
        for notebook in api.get_notebooks(assignment_stats["assignment_name"])
    }

    assignment_max_score = api.get_assignment(assignment_stats["assignment_name"])[
        "max_score"
    ]
    print(
        f"\nAssignment \"{assignment_stats['assignment_name']}\" has average score: "
        f"{api.gradebook.average_assignment_score(assignment_stats['assignment_name']):.2f}"
        f"/{assignment_max_score}"
    )
    for notebook in assignment_stats["notebooks"]:
        try:
            average_notebook_score = api.gradebook.average_notebook_score(
                notebook, assignment_stats["assignment_name"]
            )
            print(
                f'Notebook "{notebook}" has average score: '
                f"{average_notebook_score:.2f}"
                f"/{nb_max_scores[notebook]}"
            )
        except MissingEntry:
            logger.debug(f"Student didn't submit notbook {notebook}")

    print("")


def get_assignment_statistics(api, paths, students, assignment_name, local_time):
    api_assignment = api.get_assignment(assignment_name)
    if api_assignment is None:
        logger.error(f"Assignment {assignment_name} not found.")
        raise ValueError(f"Assignment {assignment_name} not found.")

    max_score = api.get_assignment(assignment_name)["max_score"]
    assignment_statistics = {}

    assignment_key = f"{assignment_name} (max: {max_score})"

    nb_max_scores = {
        notebook["name"]: notebook["max_score"]
        for notebook in api.get_notebooks(assignment_name)
    }

    for student in students:
        student_stats = get_student_assignment_scores(api, student, assignment_name)
        student_stats["fetched"] = student_fetched(
            paths["root_dir"], assignment_name, student
        )
        student_stats["attempted"] = student_attempted(
            student, paths["root_dir"], assignment_name, paths["current_admin_outbound"]
        )
        student_stats["submitted"] = student_submitted(
            student,
            paths["home_dir"],
            assignment_name,
            paths["root_dir"],
            paths["course_exchange_student"],
        )[0]

        for notebook in student_stats["notebook_scores"]:
            student_stats[f"{notebook} (max: {nb_max_scores[notebook]})"] = (
                student_stats["notebook_scores"][notebook]
            )

        student_stats.pop("notebook_scores", None)
        student_stats[assignment_key] = student_stats.pop("assignment_score", None)

        assignment_statistics[student] = student_stats

    assignment_df = pd.DataFrame.from_dict(assignment_statistics).transpose()
    assignment_df["student"] = assignment_df.index
    assignment_df.to_csv(
        f"{os.path.join(paths['stats_dir'], assignment_name)}_{local_time}.csv",
        index=False,
    )

    return assignment_key, assignment_statistics
