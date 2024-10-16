FROM python:3.11-slim

WORKDIR /action

COPY upload_to_drive.py /action/upload_to_drive.py
COPY requirements.txt /action/requirements.txt

RUN pip install --no-cache-dir -r /action/requirements.txt

ENTRYPOINT ["python", "/action/upload_to_drive.py"]
