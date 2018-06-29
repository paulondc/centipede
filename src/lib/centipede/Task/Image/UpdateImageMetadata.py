import os
from datetime import datetime
from ..Task import Task

class UpdateImageMetadata(Task):
    """
    Updates the image metadata using oiio.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a UpdateImageMetadata task.
        """
        super(UpdateImageMetadata, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        for pathCrawler in self.pathCrawlers():
            targetFilePath = self.filePath(pathCrawler)

            # converting image using open image io
            inputImageFilePath = pathCrawler.var('filePath')
            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            # updating umedia metadata
            self.updateUmediaMetadata(inputSpec, pathCrawler)

            # writing image with updated metadata
            outImage = oiio.ImageOutput.create(targetFilePath)
            outImage.open(
                targetFilePath,
                inputSpec,
                oiio.ImageOutputOpenMode.Create
            )

            outImage.copy_image(imageInput)
            outImage.close()

        # default result based on the target filePath
        return super(UpdateImageMetadata, self)._perform()

    @classmethod
    def updateUmediaMetadata(cls, spec, crawler, customMetadata={}):
        """
        Update the spec with the image metadata information.
        """
        defaultMetadata = {
            'sourceFile': crawler.var('filePath'),
            'fileUpdatedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'uverVersion': os.environ.get('UVER_VERSION', ''),
            'centipedeUser': os.environ['USERNAME'],
            'centipedeVersion': os.environ.get('UVER_CENTIPEDE_VERSION', ''),
        }

        # default metadata
        for name, value in defaultMetadata.items():
            spec.attribute(
                'umedia:{0}'.format(name),
                value
            )

        # custom metadata
        for name, value in customMetadata.items():
            spec.attribute(
                'umedia:{0}'.format(name),
                value
            )


# registering task
Task.register(
    'updateImageMetadata',
    UpdateImageMetadata
)