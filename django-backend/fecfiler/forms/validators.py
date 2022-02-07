import os
import magic
from django.core.exceptions import ValidationError


def validate_is_pdf(file):
    valid_mime_types = ["application/pdf"]
    file_mime_type = magic.from_buffer(file.read(1024), mime=True)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(
            "This is not a pdf file type. Kindly open your document using a pdf reader before uploading it."
        )
    valid_file_extensions = [".pdf"]
    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_file_extensions:
        raise ValidationError(
            "Unacceptable file extension. Only files with .pdf extensions are accepted."
        )
    if file._size > 33554432:
        raise ValidationError(
            "The File size is more than 32 MB. Kindly reduce the size of the file before you upload it."
        )
