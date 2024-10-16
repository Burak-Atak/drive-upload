import os
import json

from google.auth import load_credentials_from_file
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class DriveUploader:
    def __init__(self, google_credentials_file_path):
        self.drive_service = self.authenticate_google(google_credentials_file_path)

    def authenticate_google(self, google_credentials_file_path):
        credentials, project_id = load_credentials_from_file(
            google_credentials_file_path,
            scopes=[
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.metadata'
            ]
        )
        access_token = credentials.token

        if not access_token or credentials.expired:
            credentials.refresh(Request())
        return build("drive", "v3", credentials=credentials)

    def create_file(self, **kwargs):

        file = self.drive_service.files().create(
            **kwargs
        ).execute()

        return file.get('id')

    def update_file(self, **kwargs):
        file = self.drive_service.files().update(
            **kwargs
        ).execute()

        return file.get('id')

    def upload_files(self, files_to_create, drive_folder_id, files_to_update, file_ids_to_update):

        files_to_upload = []
        for file_path in files_to_create:
            files_to_upload.append(
                {
                    "method": self.create_file,
                    "params": {
                        "media_body": MediaFileUpload(file_path),
                        "body": {
                            'name': os.path.basename(file_path),
                            'parents': [drive_folder_id]
                        },
                        "fields": 'id'
                    },
                    "file": file_path
                }
            )

        for file_path, file_id in zip(files_to_update, file_ids_to_update):
            files_to_upload.append(
                {
                    "method": self.update_file,
                    "params": {
                        "media_body": MediaFileUpload(file_path),
                        'fileId': file_id,
                        "fields": 'id'
                    },
                    "file": file_path
                }
            )

        uploaded_files = []
        for file in files_to_upload:
            id = file["method"](**file["params"])
            uploaded_files.append({"file": file["file"], "id": id})

        return uploaded_files


if __name__ == "__main__":
    google_credentials_file_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    files_to_create = os.getenv("INPUT_FILES_TO_CREATE", "")
    drive_folder_id = os.getenv("INPUT_DRIVE_FOLDER_ID", "")
    files_to_update = os.getenv("INPUT_FILES_TO_UPDATE", "")
    file_ids_to_update = os.getenv("INPUT_FILE_IDS_TO_UPDATE", "")

    files_to_create = files_to_create.split(",") if files_to_create else []
    files_to_update = files_to_update.split(",") if files_to_update else []
    file_ids_to_update = file_ids_to_update.split(",") if file_ids_to_update else []

    assert len(files_to_update) == len(file_ids_to_update), "The number of files to update and their IDs must match"
    if files_to_create:
        assert drive_folder_id, "A folder ID is required to create files"

    uploader = DriveUploader(google_credentials_file_path)
    uploaded_files = uploader.upload_files(files_to_create, drive_folder_id, files_to_update, file_ids_to_update)

    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        output_file.write(f"uploaded_files_to_drive={json.dumps(uploaded_files)}\n")
