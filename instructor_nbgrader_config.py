import os

c = get_config()

course_name = "course"

c.Exchange.course_id = course_name
c.CourseDirectory.course_id = course_name
c.CourseDirectory.root = os.path.expanduser("~/" + course_name)
c.Exchange.root = os.path.expanduser("~/exchange")

c.ClearSolutions.code_stub = {
    "python": "### START ANSWER HERE ###\n### END ANSWER HERE ###"
}
