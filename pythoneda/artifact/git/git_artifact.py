"""
pythoneda/artifact/git/git_artifact.py

This file declares the GitArtifact class.

Copyright (C) 2023-today rydnr's pythoneda-artifact/git

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from pythoneda import attribute, listen, sensitive, Event, EventEmitter, EventListener, Ports
from pythoneda.shared.artifact_changes import Change
from pythoneda.shared.artifact_changes.events import ChangeStagingCodeDescribed, ChangeStagingCodeRequested
from pythoneda.shared.code_requests import PythonedaDependency
from pythoneda.shared.code_requests.jupyter import JupyterCodeRequest
from pythoneda.shared.git import GitDiff, GitRepo
from typing import List, Type

class GitArtifact(EventListener):
    """
    Domain of Git-based artifacts.

    Class name: GitArtifact

    Responsibilities:
        - Reacts to requests regarding Git artifacts.

    Collaborators:
        - PythonEDA realms.
    """

    _singleton = None

    def __init__(self):
        """
        Creates a new GitArtifact instance.
        """
        super().__init__()

    @classmethod
    def instance(cls):
        """
        Retrieves the singleton instance.
        :return: Such instance.
        :rtype: pythoneda.artifact.git.GitArtifact
        """
        if cls._singleton is None:
            cls._singleton = cls.initialize()

        return cls._singleton

    @classmethod
    @listen(ChangeStagingCodeRequested)
    async def listen_ChangeStagingCodeRequested(cls, event: ChangeStagingCodeRequested) -> ChangeStagingCodeDescribed:
        """
        Gets notified of a ChangeStagingCodeRequested event.
        Emits a ChangeStagingCodeDescribed event.
        :param event: The event.
        :type event: pythoneda.realm.rydnr.events.ChangeStagingCodeRequested
        :return: A request to stage changes.
        :rtype: pythoneda.shared.artifact_changes.events.ChangeStagingCodeDescribed
        """
        event_emitter = Ports.instance().resolve(EventEmitter)
        code_request = JupyterCodeRequest()
        dependencies = [
            PythonedaDependency("pythoneda-shared-pythoneda-domain", "0.0.1a38", "github:pythoneda-shared-pythoneda/domain-artifact/0.0.1a38?dir=domain"),
            PythonedaDependency("pythoneda-shared-git-shared", "0.0.1a15", "github:pythoneda-shared-git/shared-artifact/0.0.1a15?dir=shared"),
        ]

        introduction = f"""
        # Git add
        This is a request to add changes to the staging area in {event.change.repository_folder} (cloned from {event.change.repository_url}, branch {event.change.branch}).
        The changes are the following:
        {event.change.unidiff_text}
        """
        code_request.append_markdown(introduction)
        git_import_description = f"""
        ## Dependencies
        This code requires some dependencies from https://github.com/pythoneda-shared-git/shared:
        """
        code_request.append_markdown(git_import_description)
        git_import_code = f"""
        import logging
        from pythoneda.shared.git import GitAdd, GitAddFailed, GitApply, GitApplyFailed, GitStash, GitStashFailed
        import tempfile

        no_error_so_far = True
        """
        code_request.append_code(git_import_code, dependencies)
        create_diff_description = f"""
        ## Creating the diff file
        The contents we want to add to the staging area are as follows:
        ```
        {event.change.patch_set}
        ```
        """
        code_request.append_markdown(create_diff_description)
        create_diff_code = f"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=True) as tmpfile:
            tmpfile.write(""" + '"""' + """
        {event.change.patch_set}
        """ + '""")'
        code_request.append_code(create_diff_code, dependencies)
        git_stash_push_description = f"""
        ## git stash
        Git stash lets us keep the current changes in a safe place.
        """
        code_request.append_markdown(git_stash_push_description)
        git_stash_push_code = f"""
            stash_id = ""
            try:
                stash_id = GitStash("{event.change.repository_folder}").push()
            except GitStashFailed as err:
                no_error_so_far = False
                logging.getLogger("{event.id}").error(err)
        """
        code_request.append_code(git_stash_push_code, dependencies)
        git_apply_description = """
        ## git apply
        Now, lets apply the requested changes to the repository.
        """
        code_request.append_markdown(git_apply_description)
        git_apply_code = f"""
            if no_error_so_far:
                try:
                    GitApply("{event.change.repository_folder}").apply()
                except GitApplyFailed as err:
                    no_error_so_far = False
                    logging.getLogger("{event.id}").error(err)
        """
        code_request.append_code(git_apply_code, dependencies)
        git_add_description = f"""
        ## git add
        Finally, we need to add the changes to the staging area.
        """
        code_request.append_markdown(git_add_description)
        git_add_code = f"""
            if no_error_so_far:
                try:
                    GitAdd("{event.change.repository_folder}").add()
                except GitAddFailed as err:
                    no_error_so_far = False
                    logging.getLogger("{event.id}").error(err)
        """
        code_request.append_code(git_add_code, dependencies)
        result = ChangeStagingCodeDescribed(code_request, event.id)
        GitArtifact.logger().info(f"Emitting {result}")
        await event_emitter.emit(result)
        return result
