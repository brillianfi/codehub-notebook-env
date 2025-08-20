# `codehub-notebook-env`

This repository contains the Dockerfile defining the notebook environemnt for
all users of the CodeHub platform including the admin exclusive `cds` CLI used
for course management.

## Requirements

Developing the notebook environment and the `cds` CLI requires the following:

- [git](https://www.git-scm.com)
- [conda](https://docs.conda.io/en/latest/)

## Installation

The `cds` CLI is preinstalled in the notebook environment for all admin users of
CodeHub and therefore there is no installation necessary. In order to develop
the notebook environment or the `cds` CLI do the following:

1. Clone the repository using Git.
2. Inside the repository's root folder, create a Conda environment with the
   required development requirements installed with the following command:

   ```sh
   conda env create -f dev_environment.yml
   ```

3. Activate the newly created Conda environment by running:

   ```sh
   conda activate codehub-notebook-env
   ```

## Usage

To use the `cds` CLI on CodeHub log in as an admin user and open a terminal
session. The main entrypoint for the CLI is the command `cds`. For some more
information on this command as well as a list of available subcommands you can
run

```sh
cds --help
```

Available subcommands are the following:

1. `init`: Used to initialize the course for the current admin. Creates the
   folder `course/source` to contain the source notebooks for assignments. For more information about this command run

   ```sh
   cds init --help
   ```

2. `send`: Used for sending files or entire directories to other users. Requires
   a path to a file or directory somewhere in your home directory
   `/home/jovyan`. Accepts the name of a CodeHub user using the option `-u
<user>` or `--user <user>`. The `--user` option can be supplied multiple
   times. If no `--user` is given it will send the file or directory to all
   CodeHub users. If `--user` is specified at least once it will only send the
   file or directory to the specified users. For more information about this
   subcommand run:

   ```sh
   cds send --help
   ```

3. `cds assignment`: Subcommand for a grouping of commands relating to
   assignmetns. For more information about this command and a list of
   subcommands run:

   ```sh
   cds assignment --help
   ```

Subcommands of the `assignment` subcommand are the following:

1. `generate`: Used for creating the compiled assignment notebooks from the
   source notebooks. Requires the name of an assignment. For more information
   about this subcommand run:

   ```sh
   cds assignment generate --help
   ```

2. `release`: Used for releasing an assignment, adding it to `nbgrader` and
   preparing it for distribution to students. Requires the name of an
   assignment. For more information about this subcommand run:

   ```sh
   cds assignment release --help
   ```

3. `distribute`: Used for sending a released assignment to CodeHub users.
   Requires the name of an assignment. Accepts the name of a CodeHub user using
   the option `-u <user>` or `--user <user>`. The `--user` option can be
   supplied multiple times. If no `--user` is given it will send the assignment
   to all CodeHub users. If `--user` is specified at least once it will only
   send the assignment to the specified users. For more information about this
   subcommand run:

   ```sh
   cds assignment distribute --help
   ```

4. `collect`: Used for collecting submitted assignments from CodeHub users.
   Requires the name of an assignment. Accepts the name of a CodeHub user using
   the option `-u <user>` or `--user <user>`. The `--user` option can be
   supplied multiple times. If no `--user` is given it will collect the
   assignment from all CodeHub users. If `--user` is specified at least once it
   will only collect the assignment from the specified users. For more
   information about this subcommand run:

   ```sh
   cds assignment collect --help
   ```

5. `autograde`: Used for grading collected assignments. Requires the name of an
   assignment. Accepts the name of a CodeHub user using the option `-u <user>`
   or `--user <user>`. The `--user` option can be supplied multiple times. If no
   `--user` is given it will grade the assignment for all CodeHub users. If
   `--user` is specified at least once it will only grade the assignment for the
   specified users. For more information avout this subcommand run:

   ```sh
   cds assignment autograde --help
   ```

6. `feedback`: Used for sending feedback for graded assignments. Requires the
   name of an assignment. Accepts the name of a CodeHub user using the option
   `-u <user>` or `--user <user>`. The `--user` option can be supplied multiple
   times. If no `--user` is given it will send feedback for the assignment to
   all CodeHub users. If `--user` is specified at least once it will only send
   feedback for the assignment to the specified users. For more information
   avout this subcommand run:

   ```sh
   cds assignment feedback --help
   ```

7. `generalstats`: Prints statistics about an assignment. Requires the name of
   an assignment as an argument. For more information about this subcommend run:

   ```sh
   cds assignment generalstats --help
   ```

8. `csvstats`: Used for creating assignment statistics in csv format. Accepts
   the name of an assignment as an argument. If no assignment is given it will
   generate statistics for all assignments. For more information about this
   subcommend run:

   ```sh
   cds assignment csvstats --help
   ```

9. `remove`: Removes an assignment from the `nbgrader` gradebook. Requires the
   name of an assignment. For more information about this subcommand run:

   ```sh
   cds assignment remove --help
   ```

### Course management

The following is a workflow for starting and running a course on CodeHub using the `cds` CLI:

1. `cds init`
   - This will initialize the course directory structure.
2. Create assignments in your `course/source` directory. Each assignment should
   have its own directory with one or more notebooks. For example:

   ```sh
   course/
       source/
           assignment1/
               notebook1.ipynb
               notebook2.ipynb
           assignment2/
               notebook1.ipynb
   ```

3. `cds assignment generate <assignment name>`
   - This will generate the student version of the assignment
   - Note that `<assignment name>` must be the name of the assignment directory
     in your `course/source` directory.
4. `cds assignment release <assignment name>`
   - This will move the student version of the assignment to your
     `exchange/course/outbound/` directory, allowing it to be distributed to
     students
5. `cds send <file or directory>`
   - Send any required files or directories to the other users, for example data
     needed to complete the assignments.
6. `cds assignment distribute <assignment name>`
   - This will distribute your assignment from your `exchange/course/outbound/`
     directory to the corresponding directories of the other users. For students
     this is `.exchange/course/outbound/` and for admins this is
     `exchange/course/outbound`.
7. Let the students fetch, attempt and submit the assignment.
   - Fetch by:
     - Click Assignments --> Click `Fetch` on the assignment you want to fetch.
   - Attempt by:
     - Do the notebooks in the Assignment.
   - Submit by:
     - Click Assignments --> Click `Submit` on the assignment you want to
       submit.
8. `cds assignment collect <name-of-assignment>`
   - This will collect the specified assignment from each user that has
     submitted it.
9. `cds assignment autograde <assignment name>`
   - This will run the autograder for the assignment for all users' submissions
     that have been collected.
10. `cds assignment feedback <assignment name>`

- This will generate feedback for the assignments for all submissions that
  have been autograded.

11. Repeat step 3-10 for each assignment.
12. `cds assignment csvstats <OPTIONAL: assignment name>`
    - This command will generate specific statistics for each assignment for
      every student and put it in CSV files in the `stats` directory.
    - For each assignment `<assignment name>` a CSV file `<assignment name>.csv`
      will be generated which includes information on whether the student
      fetched the assignment, attempted it, submitted it, the total score
      achieved for the assignment and individual notebook score.
    - Additionally, another CSV `summary.csv` file will be generated for all the
      assignments which contains the total score for each student on all
      assignments.
    - Optionally the name of a specific assignment can be provided and the
      command will then generate statistics only for that assignment.

Note that as an instructor you have sudo access to the whole filesystem (for all
instructors and students). Each user's home directory exists in the `/efs/home/`
directory, which requires root privileges to access. You also have access to
other users' notebook servers through the admin panel.

### Development of a new notebook environment.

You need to enable the Artifact Registry service in your gcp project. Make sure that you add the following permissions to your service account: "Artifact Registry Administrator" and "Storage Admin".

1. Create a repository called "codehub".
   1.1 Choose the "Docker" format and a region that is closest to you (e.g Stockholm -> europe-north2).

2. Authenticate with Artifact Repository:

```
gcloud auth configure-docker europe-north2-docker.pkg.dev
```

3. Build and push the Docker image with correct tag to the Docker registry at
   `europe-north2-docker.pkg.dev/<project_id>/codehub/jupyter-env`
   ```
   docker build --no-cache --platform=linux/amd64 -t codehub/jupyter-env:<tag_name> .
   gcloud builds submit --region=europe-north2 --tag europe-north2-docker.pkg.dev/<project_id>/codehub/jupyter-env:<tag_name>
   ```
   Note that the default tag for codehub deployments is `stable`.

## Development

### Branches

There are two main branches:

- `develop`: Development branch. Changes to the repository are frequently merged
  into the `develop` branch by pull requests from temporary branches after
  review.
- `master`: The current release of the repository. Can only be changes by
  merging a pull request from the `develop` branch after review.

Temporary branches conform to the following naming convention:

- `bugfix/XYZ`: Designated for bugfixes.
- `feature/XYZ`: Designated for addition of new features.
- `refactor/XYZ`: Designated for refactoring work.
- `docs/XYZ`: Designated for updates to the documentation.

`XYZ` should be descriptive enough to identify what the changes relate to.

### Workflow

Use the following workflow when solving an issue:

1. Make sure you are on the `develop` branch and that you have pulled all the
   latest changes to your local git repository.
2. Create a new temporary branch from the `develop` branch following the above
   naming convention using e.g.

   ```sh
   git switch -c feature/XYZ
   ```

3. Make and commit your changes to the temporary branch.
4. Push your temporary branch to the repository.
5. Open a pull request to merge the changes from your temporary branch into the
   `develop` branch. Make sure to request at least one reviewer and mention
   which issue will be closed by this pull request.
6. After the changes have been accepted by the reviewer, merge the changes and
   delete the temporary branch after merging.

When preparing for a release use the following workflow:

1. Make sure all intended changes are merged into `develop`.
2. Create a pull request to merge changes from `develop` into `testing` with all
   current developers as reviewers.
3. Merge the changes after the review is accepted.
4. Test the current state of the repository thoroughly to make sure everything
   works as intended. If any issues are found make the changes to the `develop`
   branch and repeat step 2.
5. Create a pull request to merge `testing` into `master` with all current
   developers as reviewers.
6. Merge the changes after the review is accepted.
7. Create a new release tag on the `master` branch.
8. Merge the release tag back into `develop` for continued development.
