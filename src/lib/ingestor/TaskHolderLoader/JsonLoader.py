import json
import sys
import os
import glob
from ..Task import Task
from ..Template import Template
from ..PathCrawlerMatcher import PathCrawlerMatcher
from ..TaskHolder import TaskHolder
from ..TaskWrapper import TaskWrapper
from .TaskHolderLoader import TaskHolderLoader

class UnexpectedtContentError(Exception):
    """Unexpected content error."""

class InvalidFileError(Exception):
    """Invalid file Error."""

class InvalidDirectoryError(Exception):
    """Invalid directory Error."""

class JsonLoader(TaskHolderLoader):
    """
    Loads configuration from json files.
    """

    def addFromJsonFile(self, fileName):
        """
        Add json from a file.

        The json file need to follow the format expected
        by {@link addFromJson}.
        """
        # making sure it's a valid file
        if not (os.path.exists(fileName) and os.path.isfile(fileName)):
            raise InvalidFileError(
                'Invalid file "{0}"!'.format(fileName)
            )

        with open(fileName, 'r') as f:
            contents = '\n'.join(f.readlines())
            self.addFromJson(
                contents,
                os.path.dirname(fileName),
                os.path.basename(fileName),
            )

    def addFromJsonDirectory(self, directory):
        """
        Add json from inside of a directory with json files.

        The json file need to follow the format expected
        by {@link addFromJson}.
        """
        # making sure it's a valid directory
        if not (os.path.exists(directory) and os.path.isdir(directory)):
            raise InvalidDirectoryError(
                'Invalid directory "{0}"!'.format(directory)
            )

        # collecting the json files and loading them to the loader.
        for fileName in glob.glob(os.path.join(directory, '*.json')):
            self.addFromJsonFile(fileName)

    def addFromJson(self, jsonContents, configPath, configName=''):
        """
        Add taskHolders from json.

        Expected format:
        {
          "scripts": [
            "*/*.py"
          ],
          "vars": {
            "prefix": "/tmp/test",
            "__uiHintSourceColumns": [
                "shot",
                "type"
            ]
          },
          "taskHolders": [
            {
              "task": "convertImage",
              "targetTemplate": "{prefix}/060_Heaven/sequences/{seq}/{shot}/online/publish/elements/{plateName}/(plateNewVersion {prefix} {seq} {shot} {plateName})/{width}x{height}/{shot}_{plateName}_(plateNewVersion {prefix} {seq} {shot} {plateName}).(pad {frame} 4).exr",
              "matchTypes": [
                "dpxPlate"
              ],
              "matchVars": {
                "imageType": [
                  "sequence"
                ]
              },
              "taskHolders": [
                {
                  "task": "movGen",
                  "targetTemplate": "{prefix}/060_Heaven/sequences/{seq}/{shot}/online/review/{name}.mov",
                  "matchTypes": [
                    "exrPlate"
                  ],
                  "matchVars": {
                    "imageType": [
                      "sequence"
                    ]
                  }
                }
              ]
            }
          ]
        }
        """
        contents = json.loads(jsonContents)

        # root checking
        if not isinstance(contents, dict):
            raise UnexpectedtContentError('Expecting object as root!')

        # loading scripts
        if 'scripts' in contents:

            # scripts checking
            if not isinstance(contents['scripts'], list):
                raise UnexpectedtContentError('Expecting a list of scripts!')

            for script in contents['scripts']:
                scriptFiles = glob.glob(os.path.join(configPath, script))

                for scriptFile in scriptFiles:
                    try:
                        exec(open(scriptFile).read(), globals())
                    except Exception as err:
                        sys.stderr.write('Error on executing script: "{0}"\n'.format(
                            scriptFile
                        ))

                        raise err

        vars = {}
        if 'vars' in contents:
            # vars checking
            if not isinstance(contents['vars'], dict):
                raise UnexpectedtContentError('Expecting a list of vars!')
            vars = dict(contents['vars'])

        vars['configPath'] = configPath
        vars['configName'] = configName

        self.__loadTaskHolder(contents, vars)

    def __loadTaskHolder(self, contents, vars, parentTaskHolder=None):
        """
        Load a task holder contents.
        """
        # loading task holders
        if 'taskHolders' in contents:

            # task holders checking
            if not isinstance(contents['taskHolders'], list):
                raise UnexpectedtContentError('Expecting a list of task holders!')

            for taskHolderInfo in contents['taskHolders']:

                # task holder info checking
                if not isinstance(taskHolderInfo, dict):
                    raise UnexpectedtContentError('Expecting an object to describe the task holder!')

                task = Task.create(taskHolderInfo['task'])

                # setting task options
                if 'taskOptions' in taskHolderInfo:
                    for taskOptionName, taskOptionValue in taskHolderInfo['taskOptions'].items():
                        task.setOption(taskOptionName, taskOptionValue)

                # getting the target template
                targetTemplate = Template(taskHolderInfo['targetTemplate'])

                # getting path crawler matcher
                pathCrawlerMatcher = PathCrawlerMatcher(
                    taskHolderInfo['matchTypes'],
                    taskHolderInfo['matchVars']
                )

                # creating a task holder
                taskHolder = TaskHolder(
                    task,
                    targetTemplate,
                    pathCrawlerMatcher
                )

                # task wrapper
                if 'taskWrapper' in taskHolderInfo:
                    taskWrapper = TaskWrapper.create(taskHolderInfo['taskWrapper'])

                    # looking for task wrapper options
                    if 'taskWrapperOptions' in taskHolderInfo:
                        for optionName, optionValue in taskHolderInfo['taskWrapperOptions'].items():
                            taskWrapper.setOption(optionName, optionValue)

                    # setting task wrapper to the holder
                    taskHolder.setTaskWrapper(taskWrapper)

                # adding variables to the task holder
                for varName, varValue in vars.items():
                    taskHolder.addCustomVar(varName, varValue)

                if parentTaskHolder:
                    parentTaskHolder.addSubTaskHolder(
                        taskHolder
                    )
                else:
                    self.addTaskHolder(taskHolder)

                # loading sub task holders recursevely
                if 'taskHolders' in contents:
                    self.__loadTaskHolder(taskHolderInfo, vars, taskHolder)
