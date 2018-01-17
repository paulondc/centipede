import os
import json
from ..Crawler.Fs import Path
from collections import OrderedDict

# compatibility with python 2/3
try:
    basestring
except NameError:
    basestring = str

class TaskTypeNotFoundError(Exception):
    """Task type not found error."""

class InvalidPathCrawlerError(Exception):
    """Invalid path crawler Error."""

class TaskInvalidOptionError(Exception):
    """Task invalid option error."""

class Task(object):
    """
    Abstract Task.

    A task is used to operate over file paths resolved by the template runner.
    """

    __registered = {}

    def __init__(self, taskType):
        """
        Create a task object.
        """
        self.__pathCrawlers = OrderedDict()
        self.__options = {}
        self.__taskType = taskType

    def type(self):
        """
        Return the task type.
        """
        return self.__taskType

    def option(self, name):
        """
        Return a value for an option.
        """
        if name not in self.__options:
            raise TaskInvalidOptionError(
                'Invalid option name: "{0}"'.format(
                    name
                )
            )

        return self.__options[name]

    def setOption(self, name, value):
        """
        Set an option to the task.
        """
        self.__options[name] = value

    def optionNames(self):
        """
        Return a list of the option names.
        """
        return list(self.__options.keys())

    def filePath(self, pathCrawler):
        """
        Return the file path for path crawler.
        """
        if pathCrawler not in self.__pathCrawlers:
            raise InvalidPathCrawlerError(
                'Path crawler is not part of the task!'
            )

        return self.__pathCrawlers[pathCrawler]

    def pathCrawlers(self):
        """
        Return a list of path crawlers associated with the task.
        """
        return list(self.__pathCrawlers.keys())

    def add(self, pathCrawler, filePath):
        """
        Add a file path associate with a path crawler to the Task.
        """
        assert isinstance(pathCrawler, Path), \
            "Invalid Path Crawler!"

        assert isinstance(filePath, basestring), \
            "FilePath needs to be defined as string"

        self.__pathCrawlers[pathCrawler] = filePath

    def run(self):
        """
        Run the task.
        """
        for pathCrawler in self._perform():

            # making sure the task implementations are yielding properly.
            assert (pathCrawler in self.pathCrawlers()), \
                'Invalid path crawler!'

            yield pathCrawler

    def clone(self):
        """
        Clone the current task.
        """
        clone = self.__class__(self.type())

        # copying options
        for optionName in self.optionNames():
            clone.setOption(optionName, self.option(optionName))

        # copying path crawlers
        for pathCrawler in self.pathCrawlers():
            clone.add(pathCrawler, self.filePath(pathCrawler))

        return clone

    def toJson(self):
        """
        Serialize a task to json (it can be loaded later through createFromJson).
        """
        contents = {
            "type": self.type(),
            "options": {},
            "jsonConfigPath": "",
            "configName": "",
            "pathCrawlerData": []
        }

        # current options
        for optionName in self.optionNames():
            contents["options"][optionName] = self.option(optionName)

        # crawlers
        for pathCrawler in self.pathCrawlers():

            # we can expect all crawlers in the task to have the same configPath
            # and configName (when defined)
            if not contents['jsonConfigPath'] and 'configName' in pathCrawler.varNames():
                contents['jsonConfigPath'] = os.path.join(
                    pathCrawler.var("configPath"),
                    pathCrawler.var("configName")
                )

            contents['pathCrawlerData'].append({
                'filePath': self.filePath(pathCrawler),
                'serializedPathCrawler': pathCrawler.toJson()
            })

        return json.dumps(contents)

    @staticmethod
    def register(name, taskClass):
        """
        Register a task type.
        """
        assert issubclass(taskClass, Task), \
            "Invalid task class!"

        Task.__registered[name] = taskClass

    @staticmethod
    def registeredNames():
        """
        Return a list of registered tasks.
        """
        return list(Task.__registered.keys())

    @staticmethod
    def create(taskType, *args, **kwargs):
        """
        Create a task object.
        """
        if taskType not in Task.__registered:
            raise TaskTypeNotFoundError(
                'Task name is not registed: "{0}"'.format(
                    taskType
                )
            )
        return Task.__registered[taskType](taskType, *args, **kwargs)

    @staticmethod
    def createFromJson(jsonContents):
        """
        Factory a task based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        taskType = contents["type"]
        taskOptions = contents["options"]
        pathCrawlerData = contents["pathCrawlerData"]
        jsonConfigPath = contents["jsonConfigPath"]

        # loading json config which may load custom crawlers, expressions etc...
        if jsonConfigPath:
            from ..TaskHolderLoader import JsonLoader
            JsonLoader().addFromJsonFile(jsonConfigPath)

        task = Task.create(taskType)

        # setting task options
        for optionName, optionValue in taskOptions.items():
            task.setOption(optionName, optionValue)

        # adding crawlers
        for pathCrawlerDataItem in pathCrawlerData:
            filePath = pathCrawlerDataItem['filePath']
            crawler = Path.createFromJson(
                pathCrawlerDataItem['serializedPathCrawler']
            )
            task.add(crawler, filePath)

        return task

    def _perform(self):
        """
        For re-implementation: should implement the task.

        It should be implemented as generator that yields the filePath.
        """
        raise NotImplemented
