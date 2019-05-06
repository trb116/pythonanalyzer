import os

from ..decorators import task, notify_result


@task
@notify_result
def clone_repository(project, session, user_id=None):
    """Clones project's repository to Aurora folder."""
    result = {
        'session': session,
        'action': 'clone_repository',
        'user_id': user_id,
        'category': 'error'
    }

    if project.repository_path == '':
        result['message'] = """Can't clone "{0}" repository without path.""" \
            .format(project.name)
        return result

    project_path = project.get_path()
    if os.path.exists(project_path):
        result['message'] = """Can't clone "{0}" repository.""" \
            .format(project.name) + \
            """ "{0}" is exists.""".format(project_path)
        return result

    os.system('git clone {0} {1}'.format(project.repository_path, project_path))

    if not os.path.exists(project_path):
        result['message'] = """Can't clone "{0}" repository.\n""" \
            .format(project.name) + "Something gone wrong."
        return result

    result['category'] = 'success'
    result['message'] = 'Cloning "{0}" repository' \
        .format(project.name) + " has finished successfully."

    return result


@task
@notify_result
def remove_repository(project, session, user_id=None):
    """Removes project's repository in Aurora folder."""
    result = {
        'session': session,
        'action': 'remove_repository',
        'category': 'error',
        'user_id': user_id
    }
    project_path = project.get_path()
    if not os.path.exists(project_path):
        result['message'] = """Can't remove "{0}" repository.""" \
            .format(project.name) + " It's not exists."
        return result

    os.system('rm -rf {0}'.format(project_path))

    if os.path.exists(project_path):
        result['message'] = """Can't remove "{0}" repository.""" \
            .format(project.name) + " Something gone wrong."
        return result

    result['category'] = 'success'
    result['message'] = """"{0}" repository has removed successfully.""" \
        .format(project.name, project_path)
    return result
