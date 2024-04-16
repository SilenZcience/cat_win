"""
formatter
"""

import json
import xml.dom.minidom


class Formatter:
    """
    pretty format some specific file types
    """
    @staticmethod
    def format_json(content: str) -> tuple:
        """
        format the given content if it contains valid json.
        
        Parameters:
        content (str):
            the read content of a given file like
        
        Returns:
        (tuple):
            the content and an indicator if the content was formatted
        """
        try:
            return json.dumps(json.loads(content), indent=2), True
        except (json.JSONDecodeError,
                FileNotFoundError):
            return content, False

    @staticmethod
    def format_xml(content: str) -> tuple:
        """
        format the given content if it contains valid xml.
        
        Parameters:
        content (str):
            the read content of a given file like
        
        Returns:
        (tuple):
            the content and an indicator if the content was formatted
        """
        try:
            return xml.dom.minidom.parseString(content).toprettyxml(indent=' ' * 2), True
        except (xml.parsers.expat.ExpatError,
                xml.dom.DOMException,
                FileNotFoundError):
            return content, False

    @staticmethod
    def format(content: list) -> list:
        """
        format the given content.
        
        Parameters:
        content (list):
            the read content of a given file like [(prefix, line), ...]
        
        Returns:
        content (list):
            the content; like [(prefix, line), ...]
        """
        content_line = '\n'.join(x for _, x in content)

        converted_content, converted = Formatter.format_json(content_line)
        if converted:
            return [('', line) for line in converted_content.splitlines()]

        converted_content, converted = Formatter.format_xml(content_line)
        if converted:
            return [('', line) for line in converted_content.splitlines()]

        return content
