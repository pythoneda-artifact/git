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
import json
from pythoneda import (
    attribute,
    listen,
    sensitive,
    Event,
    EventEmitter,
    EventListener,
    Ports,
)
from pythoneda.shared.artifact.events.code import (
    ChangeStagingCodeDescribed,
    ChangeStagingCodeRequested,
)
from pythoneda.shared.code_requests import PythonedaDependency
from pythoneda.shared.code_requests.jupyterlab import JupyterlabCodeRequest


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
    async def listen_ChangeStagingCodeRequested(
        cls, event: ChangeStagingCodeRequested
    ) -> ChangeStagingCodeDescribed:
        """
        Gets notified of a ChangeStagingCodeRequested event.
        Emits a ChangeStagingCodeDescribed event.
        :param event: The event.
        :type event: pythoneda.realm.rydnr.events.ChangeStagingCodeRequested
        :return: A request to stage changes.
        :rtype: pythoneda.shared.artifact_changes.events.ChangeStagingCodeDescribed
        """
        code_request = JupyterlabCodeRequest()
        if event.change.unidiff_text is None:
            GitArtifact.logger().info(
                f"No changes to stage in folder {event.change.repository_folder}. Discarding request to describe "
                f"staging code"
            )
            return
        dependencies = [
            PythonedaDependency("dbus-next", "latest"),
            PythonedaDependency("grpcio", "latest"),
            PythonedaDependency("jupyterlab", "latest"),
            PythonedaDependency(
                "pythoneda-artifact-code-request-application", "latest"
            ),
            PythonedaDependency(
                "pythoneda-artifact-code-request-infrastructure", "latest"
            ),
            PythonedaDependency("pythoneda-shared-artifact-changes-events", "latest"),
            PythonedaDependency(
                "pythoneda-shared-artifact-changes-events-infrastructure", "latest"
            ),
            PythonedaDependency("pythoneda-shared-artifact-changes-shared", "latest"),
            PythonedaDependency("pythoneda-shared-code-requests-events", "latest"),
            PythonedaDependency(
                "pythoneda-shared-code-requests-events-infrastructure", "latest"
            ),
            PythonedaDependency("pythoneda-shared-code-requests-shared", "latest"),
            PythonedaDependency("pythoneda-shared-git-shared", "latest"),
            PythonedaDependency("pythoneda-shared-nix-flake-shared", "latest"),
            PythonedaDependency("pythoneda-shared-pythoneda-application", "latest"),
            PythonedaDependency("pythoneda-shared-pythoneda-banner", "latest"),
            PythonedaDependency("pythoneda-shared-pythoneda-domain", "latest"),
            PythonedaDependency("pythoneda-shared-pythoneda-infrastructure", "latest"),
            PythonedaDependency("requests", "latest"),
            PythonedaDependency("stringtemplate3", "latest"),
            PythonedaDependency("unidiff", "latest"),
        ]

        introduction = f"""
# Git add
This is a request to add changes to the staging area in {event.change.repository_folder}
(cloned from {event.change.repository_url}, branch {event.change.branch}).
The changes are the following:
```
{event.change.unidiff_text}
```
        """
        code_request.append_markdown(introduction)
        git_import_description = f"""
## Dependencies
This code requires some dependencies from https://github.com/pythoneda-shared-git/shared:
"""
        code_request.append_markdown(git_import_description)
        git_import_code = f"""
import asyncio
import logging
from pythoneda.artifact.code_request.application import PythonedaContext
from pythoneda.shared.git import GitAdd, GitAddAllFailed, GitApply, GitApplyFailed, GitStash, GitStashPushFailed
import tempfile

        """
        code_request.append_code(git_import_code, dependencies)
        create_diff_description = f"""
## Creating the diff file
To create a patch with the differences, we'll use a temporary file.
        """
        code_request.append_markdown(create_diff_description)
        create_diff_code = f"""
patchfile = tempfile.NamedTemporaryFile(mode='w+', delete=False)
patchfile.write({json.dumps(event.change.unidiff_text)})
patchfile.close()
        """
        code_request.append_code(create_diff_code, dependencies)
        git_stash_description = f"""
## git stash
Git stash lets us keep the current changes in a safe place.
        """
        code_request.append_markdown(git_stash_description)
        git_stash_push_code = f"""
stash_id = ""
try:
    stash_id = GitStash("{event.change.repository_folder}").push()
    print(stash_id)
except GitStashPushFailed as err:
    _pythoneda_no_error_so_far = False
    logging.getLogger("{event.id}").error(err)
        """
        code_request.append_code(git_stash_push_code, dependencies)
        git_apply_description = """
## git apply
Now, let's apply the requested changes to the repository.
        """
        code_request.append_markdown(git_apply_description)
        git_apply_code = f"""
try:
    GitApply("{event.change.repository_folder}").apply(patchfile.name)
except GitApplyFailed as err:
    _pythoneda_no_error_so_far = False
    logging.getLogger("{event.id}").error(err)
        """
        code_request.append_code(git_apply_code, dependencies)
        git_add_description = f"""
## git add
The last step is adding the changes to the staging area.
        """
        code_request.append_markdown(git_add_description)
        git_add_code = f"""
try:
    GitAdd("{event.change.repository_folder}").add_all()
except GitAddAllFailed as err:
    _pythoneda_no_error_so_far = False
    logging.getLogger("{event.id}").error(err)
        """
        code_request.append_code(git_add_code, dependencies)
        git_add_description = f"""
## Emit event
Finally, let's emit the event that this code has been executed successfully.
        """
        code_request.append_markdown(git_add_description)
        git_add_code = f"""
class CodeRequest(PythonedaContext):

    async def emit_event(self):
        from pythoneda import EventEmitter, Ports
        from pythoneda.shared.artifact_changes import Change
        from pythoneda.shared.artifact_changes.events import ChangeStaged

        print("Emitting ChangeStaged event")
        await Ports.instance().resolve(EventEmitter).emit(
            ChangeStaged(
                Change.from_json(
                    {json.dumps(event.change.to_json())}),
                '{event.id}'))
        print("ChangeStaged event emitted!")
import nest_asyncio
nest_asyncio.apply()
loop = asyncio.get_event_loop()
loop.run_until_complete(CodeRequest.main("{event.id}"))
        """
        code_request.append_code(git_add_code, dependencies)
        result = ChangeStagingCodeDescribed(code_request, event.id)
        GitArtifact.logger().info(f"Emitting {result}")
        await Ports.instance().resolve(EventEmitter).emit(result)
        return result
