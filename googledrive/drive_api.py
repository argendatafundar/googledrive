from dataclasses import dataclass
from logging import Logger

from polars import from_dict
from slepy.singleton import Singleton
from .http import LazyHttpRequest
from .dataclass_factory import Dataclass

from slepy.logger import LoggerFactory
from slepy.logger import inject_logger
from slepy.logger import debug_print

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from typing import Any, Callable, ClassVar, Dict, TypeVar
from typing import Optional, List
import googleapiclient.http
from functools import wraps
import os

from urllib.parse import urljoin

from tqdm.std import tqdm

BASE_SCOPE_URL = 'https://www.googleapis.com/'
DEFAULT_SCOPES = [
    '/auth/drive',
]

DEFAULT_SCOPES = [
    urljoin(BASE_SCOPE_URL, scope) 
    for scope in DEFAULT_SCOPES
]

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import io

# https://developers.google.com/drive/api/guides/manage-downloads#python
def gdrive_download_file(service, real_file_id, chunksize=1024*1024):
  """Downloads a file
  Args:
      real_file_id: ID of the file to download
  Returns : IO object with location.

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """

  try:
    request = service.files().get_media(fileId=real_file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request, chunksize=chunksize)
    done = False
    with tqdm(total=100, colour='yellow') as pbar:
        while done is False:
            status, done = downloader.next_chunk()
            # print(f"Download {int(status.progress() * 100)}.")
            pbar.update(int(status.progress() * 100) - pbar.n)
        pbar.colour = 'green'
        pbar.close()

    return file.getvalue()

  except HttpError as error:
    print(f"An error occurred: {error}")
    file = None

import requests

def download_from_response(service, response: dict):
    """
    Downloads a file from a given Google Drive file URI using an authorized service object.

    :param service: Authorized Google Drive API service object.
    :param response: Dictionary containing the response with the file URI.
    :return: BytesIO object containing the file content.
    """
    expected_schema = dict(
        name=str,
        metadata={'@type': str},
        done=bool,
        response={
            '@type': str,
            'downloadUri': str,
            'partialDownloadAllowed': bool,
        }
    )

    downloadUri = response['response']['downloadUri']

    # Get the access token from the authorized service object
    credentials = service._http.credentials
    access_token = credentials.token

    # Set the authorization header
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Initialize a bytes buffer
    buffer = io.BytesIO()

    # Send a GET request with the authorization header
    with requests.get(downloadUri, headers=headers, stream=True) as r:
        r.raise_for_status()
        # Get the total file size from the headers
        total_size = int(r.headers.get('Content-Length', 0))
        # Initialize the progress bar
        with tqdm(total=total_size, unit='B', unit_scale=True, colour='yellow') as pbar:
            # Iterate over the response in chunks
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    # Write each chunk to the buffer
                    buffer.write(chunk)
                    # Update the progress bar
                    pbar.update(len(chunk))
            pbar.colour = 'green'

    # Seek to the beginning of the buffer
    buffer.seek(0)
    return buffer.getvalue()


def authenticate_google_drive(
        client_secrets_file: str,
        credentials_file: str,
        scopes: Optional[List[str]] = None,
        port: int = 0,
        ) -> Resource:
    if scopes is None:
        scopes = DEFAULT_SCOPES
    
    creds = None
    # Check if the credentials file already exists
    if os.path.exists(credentials_file):
        creds = Credentials.from_authorized_user_file(credentials_file, scopes)
    
    # If credentials are not valid or not available, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
                creds = flow.run_local_server(port=port)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=port)
        
        # Save the credentials for future use
        with open(credentials_file, 'w') as token_file:
            token_file.write(creds.to_json())
    
    # Build and return the Google Drive service object
    service = build('drive', 'v3', credentials=creds)
    return service

class DriveFilesApi: ... # type: ignore (declaración sin implementación)
def execute_service_method(f: Callable):
        name = f.__name__
        @classmethod
        def _(cls, *args, **kwargs):
            kwargs = dict(filter(lambda x: x is not None, kwargs.items()))
            service = getattr(DriveFilesApi.instance._drive, cls.__name__)
            method = getattr(service(), name)
            result: LazyHttpRequest[Any, dict] = method(*args, **kwargs)

            return result
        
        return _

@inject_logger
class DriveFilesApi(Singleton):
    log: Logger

    def __init__(
            self, 
            auth_folder: str, 
            client_secrets_file: str = 'client_secrets.json',
            credentials_file: str = 'client_creds.json'
        ):
        self.auth_folder = auth_folder
        self._drive = authenticate_google_drive(
            client_secrets_file=os.path.join(auth_folder, client_secrets_file),
            credentials_file=os.path.join(auth_folder, credentials_file),
            port=0,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file',
            ]
        )
        self.log.info("Authenticated to Google Drive.")
    
    
    class files:
        @execute_service_method
        def list(q: str, # type: ignore
            fields: Optional[str] = '*', 
            includeItemsFromAllDrives: Optional[bool] = False, 
            supportsAllDrives: Optional[bool] = False,
            driveId: Optional[str] = None,
            corpora: Optional[str] = None,
            maxResults: Optional[int] = None,
            orderBy: Optional[str] = None,
            pageToken: Optional[str] = None,
            spaces: Optional[str] = None,
            includePermissionsForView: Optional[str] = None,
            includeLabels: Optional[str] = None
            ) -> LazyHttpRequest[Any, dict]: ...
        
        @execute_service_method
        def download(fileId: str,
                     mimeType: Optional[str] = None,
                     revisionId: Optional[str] = None
                     ) -> LazyHttpRequest[Any, bytes]: ...

        def get_contents_of(id: str, chunksize: int = 1024*1024):
            return gdrive_download_file(DriveFilesApi.instance._drive, id, chunksize=chunksize)
        
        @execute_service_method
        def get(
            fileId: str,
            acknowledgeAbuse: Optional[bool] = None,
            supportsAllDrives: Optional[bool] = None,
            supportsTeamDrives: Optional[bool] = None,
            includePermissionsForView: Optional[str] = None,
            includeLabels: Optional[str] = None
            ) -> LazyHttpRequest[Any, dict]: ...
    

    class drives:
        @execute_service_method
        def list(q: Optional[str] = None, # type: ignore
            fields: Optional[str] = '*', 
            pageSize: Optional[int] = None, 
            pageToken: Optional[str] = None
            ) -> LazyHttpRequest[Any, dict]: ...
        
    class http:
        @staticmethod
        def download_from_response(response: dict):
            return download_from_response(DriveFilesApi.instance._drive, response)

def id_summary(x: str):
    return x[:3] + '*' + x[-3:]

class ResourceRef(Dataclass(
   init=True,
   repr=False,
   eq=True,
   order=False,
   unsafe_hash=False,
   frozen=False,
   kw_only=False,
   slots=False
)):
    id: str
    name: str
    mimeType: Optional[str] = None
    trashed: Optional[bool] = None
    parents: Any = None

    from_dict: ClassVar[Callable[[Dict[str, Any]], 'ResourceRef']]
    to_dict: ClassVar[Callable[['ResourceRef'], Dict[str, Any]]]

    def __post_init__(self):
        assert len(self.parents) == 1
        self.parents = self.parents[0] if self.parents is not None else None

    def __repr__(self):
        display_id = id_summary(self.id)
        parents_ids = '' if self.parents is None else [id_summary(parent) for parent in self.parents]
        return f"ResourceRef(id={display_id}, name='{self.name}', parents={parents_ids})"
    
    def __hash__(self):
        return hash(self.id)