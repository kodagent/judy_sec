import json
import os
import pickle

from bson import ObjectId
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models


class SimilarityMatrix(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    matrix_file = models.FileField(upload_to="similarity_matrices/")
    job_ids = models.TextField(default='[]')  # Store job IDs as a JSON array
    candidate_ids = models.TextField(default='[]')  # Store candidate IDs as a JSON array

    def set_matrix(self, matrix, job_ids, candidate_ids):
        # Serialize the matrix to bytes
        matrix_bytes = pickle.dumps(matrix)

        # Define the file path
        file_path = os.path.join(settings.MEDIA_ROOT, "similarity_matrices", "matrix.pkl")

        # Check if the file already exists
        if os.path.exists(file_path):
            # Open the existing file in binary write mode and overwrite it
            with open(file_path, 'wb') as file:
                file.write(matrix_bytes)
        else:
            # If the file doesn't exist, use the save method to create it
            self.matrix_file.save("matrix.pkl", ContentFile(matrix_bytes))

        # Convert ObjectId instances to strings
        job_ids_str = [str(job_id) if isinstance(job_id, ObjectId) else job_id for job_id in job_ids]
        candidate_ids_str = [str(candidate_id) if isinstance(candidate_id, ObjectId) else candidate_id for candidate_id in candidate_ids]

        # Convert to JSON and save in fields
        self.job_ids = json.dumps(job_ids_str)
        self.candidate_ids = json.dumps(candidate_ids_str)
        self.save()

    def get_matrix(self):
        # Read the matrix bytes from the file and deserialize
        matrix_bytes = self.matrix_file.read()
        return pickle.loads(matrix_bytes)

    def get_job_ids(self):
        # Deserialize the JSON stored in job_ids field
        return json.loads(self.job_ids)

    def get_candidate_ids(self):
        # Deserialize the JSON stored in candidate_ids field
        return json.loads(self.candidate_ids)
