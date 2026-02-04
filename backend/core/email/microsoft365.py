"""
Microsoft 365 Graph API client for email operations.

Supports sending and receiving emails via shared mailboxes
using OAuth2 client credentials flow.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Microsoft Graph API endpoints
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


class Microsoft365Client:
    """
    Client for Microsoft Graph API email operations.

    Uses OAuth2 client credentials flow for application-level access.
    Supports shared mailboxes for helpdesk scenarios.

    Required Azure AD App Permissions (Application):
    - Mail.Read - Read mail in all mailboxes
    - Mail.Send - Send mail as any user
    - Mail.ReadWrite - Read and write mail (for marking as read)

    Usage:
        client = Microsoft365Client(
            tenant_id="your-tenant-id",
            client_id="your-client-id",
            client_secret="your-client-secret",
            mailbox="helpdesk@company.com"
        )

        # Send email
        await client.send_email(
            to_email="user@example.com",
            subject="Hello",
            body_html="<p>Hello World</p>"
        )

        # Fetch emails
        messages = await client.list_messages(filter_unread=True)
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        mailbox: str
    ):
        """
        Initialize Microsoft 365 client.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Client secret
            mailbox: Email address of the mailbox to use (typically a shared mailbox)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.mailbox = mailbox
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token using client credentials flow.

        Returns:
            Access token string

        Raises:
            Exception: If authentication fails
        """
        token_url = TOKEN_URL_TEMPLATE.format(tenant_id=self.tenant_id)

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code != 200:
                error_data = response.json()
                error_desc = error_data.get("error_description", "Unknown error")
                logger.error(f"M365 authentication failed: {error_desc}")
                raise Exception(f"Microsoft 365 authentication failed: {error_desc}")

            token_data = response.json()
            self._access_token = token_data["access_token"]
            return self._access_token

    async def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        if not self._access_token:
            await self._get_access_token()

        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        retry_on_401: bool = True
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Graph API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (relative to base URL)
            json_data: Optional JSON body
            retry_on_401: Whether to retry after refreshing token on 401

        Returns:
            Response JSON data

        Raises:
            Exception: If request fails
        """
        url = f"{GRAPH_API_URL}/{endpoint}"
        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Handle token expiration
            if response.status_code == 401 and retry_on_401:
                self._access_token = None
                return await self._make_request(method, endpoint, json_data, retry_on_401=False)

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    error_msg = response.text
                logger.error(f"M365 API error: {response.status_code} - {error_msg}")
                raise Exception(f"Microsoft 365 API error: {error_msg}")

            # Some endpoints return no content (204)
            if response.status_code == 204:
                return {}

            return response.json()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        from_name: Optional[str] = None,
        message_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via Microsoft Graph API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content (used if body_html is None)
            from_name: Optional display name for sender
            message_id: Optional custom Message-ID header
            headers: Optional additional headers

        Returns:
            API response data
        """
        # Build message object
        body_content = body_html or body_text or ""
        body_type = "HTML" if body_html else "Text"

        message = {
            "subject": subject,
            "body": {
                "contentType": body_type,
                "content": body_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email
                    }
                }
            ]
        }

        # Add custom headers via internetMessageHeaders
        if headers or message_id:
            internet_headers = []
            if message_id:
                internet_headers.append({
                    "name": "Message-ID",
                    "value": message_id
                })
            if headers:
                for name, value in headers.items():
                    internet_headers.append({
                        "name": name,
                        "value": value
                    })
            message["internetMessageHeaders"] = internet_headers

        # Send via user's mailbox
        endpoint = f"users/{self.mailbox}/sendMail"
        payload = {
            "message": message,
            "saveToSentItems": True
        }

        result = await self._make_request("POST", endpoint, payload)
        logger.info(f"Email sent via M365 to {to_email}")
        return result

    async def list_messages(
        self,
        folder: str = "inbox",
        filter_unread: bool = True,
        top: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List messages from mailbox.

        Args:
            folder: Mail folder (inbox, sentitems, etc.)
            filter_unread: Only return unread messages
            top: Maximum number of messages to return

        Returns:
            List of message objects
        """
        endpoint = f"users/{self.mailbox}/mailFolders/{folder}/messages"
        params = [f"$top={top}"]

        if filter_unread:
            params.append("$filter=isRead eq false")

        # Select only needed fields for list view
        params.append("$select=id,subject,from,receivedDateTime,isRead,internetMessageId")

        endpoint = f"{endpoint}?{'&'.join(params)}"
        result = await self._make_request("GET", endpoint)

        return result.get("value", [])

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get full message content by ID.

        Args:
            message_id: Message ID from list_messages

        Returns:
            Full message object including body
        """
        endpoint = f"users/{self.mailbox}/messages/{message_id}"
        return await self._make_request("GET", endpoint)

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark message as read.

        Args:
            message_id: Message ID

        Returns:
            Updated message object
        """
        endpoint = f"users/{self.mailbox}/messages/{message_id}"
        return await self._make_request("PATCH", endpoint, {"isRead": True})

    async def delete_message(self, message_id: str) -> None:
        """
        Delete message.

        Args:
            message_id: Message ID
        """
        endpoint = f"users/{self.mailbox}/messages/{message_id}"
        await self._make_request("DELETE", endpoint)

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection by fetching mailbox info.

        Returns:
            Mailbox user info

        Raises:
            Exception: If connection test fails
        """
        endpoint = f"users/{self.mailbox}"
        result = await self._make_request("GET", endpoint)
        logger.info(f"M365 connection test successful for {self.mailbox}")
        return result

    async def list_mailboxes(self) -> List[Dict[str, Any]]:
        """
        List available mailboxes/users accessible by the application.

        Note: This requires Directory.Read.All or User.Read.All permission to list users,
        or you can pass specific shared mailbox emails.

        For shared mailboxes, the app typically needs to have SendAs or FullAccess
        permission granted by the admin.

        Returns:
            List of mailbox objects with email and displayName
        """
        mailboxes = []

        try:
            # First, try to get the current mailbox user info if configured
            if self.mailbox:
                try:
                    user = await self._make_request("GET", f"users/{self.mailbox}")
                    mailboxes.append({
                        "email": user.get("mail") or user.get("userPrincipalName"),
                        "displayName": user.get("displayName", self.mailbox)
                    })
                except Exception:
                    pass  # Mailbox might not exist yet

            # Try to list users (requires appropriate permissions)
            try:
                # Get only mail-enabled users, limit to 100
                endpoint = "users?$select=mail,displayName,userPrincipalName&$filter=mail ne null&$top=100"
                result = await self._make_request("GET", endpoint)

                for user in result.get("value", []):
                    email = user.get("mail") or user.get("userPrincipalName")
                    if email and email not in [m["email"] for m in mailboxes]:
                        mailboxes.append({
                            "email": email,
                            "displayName": user.get("displayName", email)
                        })
            except Exception as e:
                # User listing might not be permitted, that's OK
                logger.debug(f"Could not list users (permission may be needed): {e}")

        except Exception as e:
            logger.error(f"Error listing mailboxes: {e}")

        return mailboxes

    async def list_folders(self, parent_folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List mail folders in the configured mailbox.

        Args:
            parent_folder_id: Optional parent folder ID to list child folders.
                            If None, lists top-level folders.

        Returns:
            List of folder objects with id, displayName, and childFolderCount
        """
        folders = []

        try:
            if parent_folder_id:
                endpoint = f"users/{self.mailbox}/mailFolders/{parent_folder_id}/childFolders"
            else:
                endpoint = f"users/{self.mailbox}/mailFolders"

            # Get folder info with message counts
            endpoint += "?$select=id,displayName,childFolderCount,totalItemCount,unreadItemCount&$top=100"
            result = await self._make_request("GET", endpoint)

            for folder in result.get("value", []):
                folders.append({
                    "id": folder.get("id"),
                    "displayName": folder.get("displayName"),
                    "childFolderCount": folder.get("childFolderCount", 0),
                    "totalItemCount": folder.get("totalItemCount", 0),
                    "unreadItemCount": folder.get("unreadItemCount", 0)
                })

            logger.info(f"Listed {len(folders)} folders for {self.mailbox}")

        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            raise

        return folders
