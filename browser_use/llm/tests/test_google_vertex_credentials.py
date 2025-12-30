import os
import json
import pytest
from unittest.mock import patch, MagicMock
from browser_use.llm.google.chat import ChatGoogle

class TestChatGoogleCredentials:
    @patch('google.oauth2.service_account.Credentials.from_service_account_file')
    @patch('google.genai.Client')
    def test_load_credentials_from_json(self, mock_client, mock_from_file):
        # Setup mock
        mock_creds = MagicMock()
        mock_from_file.return_value = mock_creds
        
        # Initialize ChatGoogle with service_account_json
        json_path = 'fake-service-account.json'
        chat = ChatGoogle(
            model='gemini-2.0-flash',
            service_account_json=json_path
        )
        
        # Trigger client creation
        client = chat.get_client()
        
        # Verify from_service_account_file was called with the correct path
        mock_from_file.assert_called_once_with(json_path)
        
        # Verify genai.Client was called with the mock credentials
        mock_client.assert_called_once()
        args, kwargs = mock_client.call_args
        assert kwargs['credentials'] == mock_creds

    @patch('google.oauth2.service_account.Credentials.from_service_account_file')
    @patch('google.genai.Client')
    def test_credentials_precedence(self, mock_client, mock_from_file):
        # Setup mock
        explicit_creds = MagicMock()
        
        # Initialize ChatGoogle with both explicit credentials and service_account_json
        chat = ChatGoogle(
            model='gemini-2.0-flash',
            credentials=explicit_creds,
            service_account_json='fake-service-account.json'
        )
        
        # Trigger client creation
        client = chat.get_client()
        
        # Verify from_service_account_file was NOT called because explicit credentials exist
        mock_from_file.assert_not_called()
        
        # Verify genai.Client was called with the explicit credentials
        mock_client.assert_called_once()
        args, kwargs = mock_client.call_args
        assert kwargs['credentials'] == explicit_creds
