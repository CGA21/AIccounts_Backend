import io
import os
import re
#from pprint import pprint
from google.cloud import vision_v1
from google.cloud import storage
from google.oauth2 import service_account

# Set path to your service account JSON
SERVICE_ACCOUNT_PATH = "plasma-ember-455216-j5-d10d914ae03c.json"

# Load credentials
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH)


def create_bucket(bucket_name):
    """Creates a new bucket."""
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.create_bucket(bucket_name)
    print(f"Bucket {bucket.name} created")


def get_vision_client():
    """Initialize and return a Google Vision API client."""
    return vision_v1.ImageAnnotatorClient(credentials=credentials)


def get_storage_client():
    """Initialize and return a Google Cloud Storage client."""
    return storage.Client(credentials=credentials)


def upload_to_gcs(bucket_name, local_file_path, destination_blob_name):
    """Upload a local file to Google Cloud Storage."""
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    return f"gs://{bucket_name}/{destination_blob_name}"


def extract_text_from_image(client, image_content):
    """Extract text from image content using Google Vision API."""
    try:
        image = vision_v1.types.Image(content=image_content)
        response = client.text_detection(image=image)
        return response.full_text_annotation.text if response.full_text_annotation else ""
    except Exception as e:
        print(f"Text extraction error: {e}")
        return None


def extract_text_from_pdf(client, gcs_uri):
    """Extract text from a PDF stored in Google Cloud Storage using Google Vision API batch processing."""
    try:
        gcs_source = vision_v1.types.GcsSource(uri=gcs_uri)
        input_config = vision_v1.types.InputConfig(gcs_source=gcs_source, mime_type="application/pdf")

        async_request = vision_v1.types.AnnotateFileRequest(
            features=[vision_v1.types.Feature(type_=vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION)],
            input_config=input_config,
        )

        response = client.batch_annotate_files(requests=[async_request])
        text = "\n".join([page.full_text_annotation.text for page in response.responses[0].responses])
        return text
    except Exception as e:
        print(f"PDF text extraction error: {e}")
        return None


def process_invoices(filename, bucket_name, folder):
    """Process multiple invoices in a given folder."""
    client = get_vision_client()
    full_path = os.path.join(folder, filename)

    if filename.endswith(".pdf"):
        gcs_uri = upload_to_gcs(bucket_name, full_path, filename)
        extracted_text = extract_text_from_pdf(client, gcs_uri)
    else:
        with io.open(full_path, 'rb') as image_file:
            image_content = image_file.read()
        extracted_text = extract_text_from_image(client, image_content)

    if extracted_text:
        #pprint(extracted_text)
        print("The text has been processed.")
        return extracted_text
    else:
        print("Text extraction failed.")
        return ""


# Example usage
# process_invoices("invoice1.pdf", "whatarethosehackuta", folder="invoices")
