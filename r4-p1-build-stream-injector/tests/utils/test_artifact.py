import unittest
import uuid

from unittest.mock import patch

from a2a.types import DataPart, Part, TextPart
from a2a.utils.artifact import (
    new_artifact,
    new_data_artifact,
    new_text_artifact,
)


class TestArtifact(unittest.TestCase):
    @patch('uuid.uuid4')
    def test_new_artifact_generates_id(self, mock_uuid4):
        mock_uuid = uuid.UUID('abcdef12-1234-5678-1234-567812345678')
        mock_uuid4.return_value = mock_uuid
        artifact = new_artifact(parts=[], name='test_artifact')
        self.assertEqual(artifact.artifact_id, str(mock_uuid))

    def test_new_artifact_assigns_parts_name_description(self):
        parts = [Part(root=TextPart(text='Sample text'))]
        name = 'My Artifact'
        description = 'This is a test artifact.'
        artifact = new_artifact(parts=parts, name=name, description=description)
        self.assertEqual(artifact.parts, parts)
        self.assertEqual(artifact.name, name)
        self.assertEqual(artifact.description, description)

    def test_new_artifact_empty_description_if_not_provided(self):
        parts = [Part(root=TextPart(text='Another sample'))]
        name = 'Artifact_No_Desc'
        artifact = new_artifact(parts=parts, name=name)
        self.assertEqual(artifact.description, '')

    def test_new_text_artifact_creates_single_text_part(self):
        text = 'This is a text artifact.'
        name = 'Text_Artifact'
        artifact = new_text_artifact(text=text, name=name)
        self.assertEqual(len(artifact.parts), 1)
        self.assertIsInstance(artifact.parts[0].root, TextPart)

    def test_new_text_artifact_part_contains_provided_text(self):
        text = 'Hello, world!'
        name = 'Greeting_Artifact'
        artifact = new_text_artifact(text=text, name=name)
        self.assertEqual(artifact.parts[0].root.text, text)

    def test_new_text_artifact_assigns_name_description(self):
        text = 'Some content.'
        name = 'Named_Text_Artifact'
        description = 'Description for text artifact.'
        artifact = new_text_artifact(
            text=text, name=name, description=description
        )
        self.assertEqual(artifact.name, name)
        self.assertEqual(artifact.description, description)

    def test_new_data_artifact_creates_single_data_part(self):
        sample_data = {'key': 'value', 'number': 123}
        name = 'Data_Artifact'
        artifact = new_data_artifact(data=sample_data, name=name)
        self.assertEqual(len(artifact.parts), 1)
        self.assertIsInstance(artifact.parts[0].root, DataPart)

    def test_new_data_artifact_part_contains_provided_data(self):
        sample_data = {'content': 'test_data', 'is_valid': True}
        name = 'Structured_Data_Artifact'
        artifact = new_data_artifact(data=sample_data, name=name)
        self.assertIsInstance(artifact.parts[0].root, DataPart)
        # Ensure the 'data' attribute of DataPart is accessed for comparison
        self.assertEqual(artifact.parts[0].root.data, sample_data)

    def test_new_data_artifact_assigns_name_description(self):
        sample_data = {'info': 'some details'}
        name = 'Named_Data_Artifact'
        description = 'Description for data artifact.'
        artifact = new_data_artifact(
            data=sample_data, name=name, description=description
        )
        self.assertEqual(artifact.name, name)
        self.assertEqual(artifact.description, description)


if __name__ == '__main__':
    unittest.main()
