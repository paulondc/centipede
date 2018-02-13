from .Lut import Lut
import re
import xml.etree.ElementTree as ElementTree

class Ccc(Lut):
    """
    Parses a Ccc file.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Ccc object.
        """
        super(Ccc, self).__init__(*args, **kwargs)

        self.__parseXML()

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a lut file.
        """
        if not super(Ccc, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'ccc'

    def __parseXML(self):
        """
        Parse the ccc XML information and assign that to the crawler.
        """
        tree = ElementTree.parse(self.var('filePath'))
        root = tree.getroot()
        namespace = self.__xmlNamespace(root)

        colorCorrection = root.find('{}ColorCorrection'.format(namespace))
        sopNode = colorCorrection.find('{}SOPNode'.format(namespace))
        error = colorCorrection.find('{}Error'.format(namespace))

        slope = sopNode.find('{}Slope'.format(namespace))
        offset = sopNode.find('{}Offset'.format(namespace))
        power = sopNode.find('{}Power'.format(namespace))

        slope = list(map(float, slope.text.split(" ")))
        offset = list(map(float, offset.text.split(" ")))
        power = list(map(float, power.text.split(" ")))

        satNode = colorCorrection.find('{}SatNode'.format(namespace))
        saturation = float(satNode.find('{}Saturation'.format(namespace)).text)

        self.setVar('slope', slope)
        self.setVar('offset', offset)
        self.setVar('power', power)
        self.setVar('saturation', saturation)

        if error is not None:
            self.setVar('error', error.text)

    @classmethod
    def __xmlNamespace(cls, element):
        """
        Return the namespace used in the xml file.
        """
        m = re.match('\{.*\}', element.tag)
        return m.group(0) if m else ''


# registering crawler
Ccc.register(
    'ccc',
    Ccc
)
