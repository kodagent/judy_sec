import os
import tempfile

import pymongo
from bs4 import BeautifulSoup
from bson import ObjectId
from django.conf import settings
from langchain.document_loaders import OnlinePDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from chatbackend.configs.logging_config import configure_logger

# Append TESSERACT_PATH to the system PATH, if it's set
if "TESSERACT_PATH" in os.environ:
    os.environ["PATH"] += os.pathsep + os.environ["TESSERACT_PATH"]

# Append POPPLER_PATH to the system PATH, if it's set
if "POPPLER_PATH" in os.environ:
    os.environ["PATH"] += os.pathsep + os.environ["POPPLER_PATH"]

logger = configure_logger(__name__)

# Initialize a MongoDB client
client = pymongo.MongoClient(settings.MONGO_DB_URL)
db = client[settings.MONGO_DB_NAME]
# print(client.list_database_names())
# print(db.list_collection_names())
# A list of all your collection names
# collections = db.list_collection_names() # Add all your collection names

# A dictionary to store potential relationships
# relationships = {}

# # Loop through each collection
# for collection_name in collections:
#     collection = db[collection_name]

#     # Get distinct IDs from each reference field (e.g., owner, applicantDetail, etc.)
#     # Note: You might want to adapt this part based on the known structure of your collections
#     for field in ['owner', 'applicantDetail', 'jobDetail']:
#         ids = collection.distinct(field)

#         # Check for matches in other collections
#         for potential_related_collection in collections:
#             if potential_related_collection == collection_name:
#                 continue

#             related_collection = db[potential_related_collection]
#             match_count = related_collection.count_documents({'_id': {'$in': ids}})
#             print("This is the match_count: ", match_count)
#             if match_count > 0:
#                 relationship_key = f"{collection_name} -> {potential_related_collection}"
#                 print("This is the relationship key", relationship_key)
#                 relationships[relationship_key] = match_count

# print(relationships)


async def get_resume_content(application_id):  # , owner_id):
    try:
        applicant = db.applications.find_one(
            {
                "_id": ObjectId(application_id),
                # "owner_id": ObjectId(owner_id)
            }
        )
        public_url = applicant["resumeDocument"] if applicant else None
        # Load PDF data
        loader = OnlinePDFLoader(public_url)
        data = loader.load()

        # Split the text for analysis
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)

        doc_list = [t.page_content for t in texts]
        doc_content = "   ".join(doc_list)

        return doc_content
    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


async def get_doc_content(
    owner_id, doc_type=None
):  # owner id rather candidate id because this could function for candidates as well as recruiters
    try:
        applicant = db.applications.find_one(
            {
                # "_id": ObjectId(applicant_id),
                "owner_id": ObjectId(owner_id)
            }
        )
        if doc_type == "CL":
            public_url = applicant["IELTSDocument"] if applicant else None
        elif doc_type == "R":
            public_url = applicant["IELTSDocument"] if applicant else None
        elif doc_type == "JP":
            public_url = applicant["IELTSDocument"] if applicant else None

        # Load PDF data
        loader = OnlinePDFLoader(public_url)
        data = loader.load()

        # Split the text for analysis
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)

        doc_list = [t.page_content for t in texts]
        doc_content = "   ".join(doc_list)

        return doc_content
    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


async def get_job_post_content_async(job_id):
    try:
        job = db.jobs.find_one(
            {
                "_id": ObjectId(job_id),
                # "owner_id": ObjectId(owner_id)
            }
        )

        # Create a temporary file and get its path
        temp_file_path = create_temporary_job_file(job)

        # Load PDF data
        loader = TextLoader(temp_file_path)
        data = loader.load()

        os.unlink(temp_file_path)

        # Split the text for analysis
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)

        doc_list = [t.page_content for t in texts]
        doc_content = "   ".join(doc_list)

        return doc_content
    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def get_job_post_content(job_id):
    try:
        job = db.jobs.find_one(
            {
                "_id": ObjectId(job_id),
                # "owner_id": ObjectId(owner_id)
            }
        )

        # Create a temporary file and get its path
        temp_file_path = create_temporary_job_file(job)

        # Load PDF data
        loader = TextLoader(temp_file_path)
        data = loader.load()

        os.unlink(temp_file_path)

        # Split the text for analysis
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)

        doc_list = [t.page_content for t in texts]
        doc_content = "   ".join(doc_list)

        return doc_content
    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


# Function to create a temporary file with job details
def create_temporary_job_file(job_data):
    with tempfile.NamedTemporaryFile(mode="w+t", delete=False) as temp_file:
        title = job_data["title"] if job_data else None
        location = job_data["location"] if job_data else None
        job_type = job_data["jobType"] if job_data else None
        description_html = job_data["overview"] if job_data else None
        description = (
            BeautifulSoup(description_html, "html.parser").get_text()
            if description_html
            else None
        )

        # Write the data to the temp file
        temp_file.write(f"Title: {title}\n")
        temp_file.write(f"Location: {location}\n")
        temp_file.write(f"Job Type: {job_type}\n")
        temp_file.write(f"Description: {description}\n")

        # Return the name of the temp file
        return temp_file.name


def run_test():
    job_id = "654194177b7c7c8236e8541f"
    get_job_post_content(job_id)


# users -> applications -> watchlists
# users -> immigrations
# users -> watchlists
# users -> interviews
# users -> applications -> interviews
# users -> immigrationsupports
# users -> meetings
# users -> tokens

# users -> jobs
# users -> jobapplications
# users -> applications -> jobapplications
# users -> jobs -> jobapplications

# applications -> licensuresupports


# {
#     '_id': ObjectId('636a7788f7024d11a1e7a4f2'),
#     'owner': ObjectId('63628cf1fb0e3725b7fd789f'),
#     'lastCompletedStage': {
#         'stageNumber': 6,
#         'stageName': 'Personal Details',
#         'completed': True,
#         'date': datetime.datetime(2022, 11, 8, 16, 43, 4, 929000)
#     },
#     'workingExperience': {
#         'yearOfExperience': 2,
#         'hasLicense': True,
#         'processingCanadaLicense': False,
#         'locationsOfActiveLicense': [
#             {
#                 'location': 'Afghanistan',
#                 'licensePin': '234566GF'
#             },
#             {
#                 'location': 'Canada',
#                 'licensePin': '2358665'
#             }
#         ]
#     },
#     'locationPreferences': {
#         'currentLocation': 'British Indian Ocean Territory',
#         'interestedProvince': 'Alberta',
#         'interestedCityInSelectedProvince': 'Airdries'
#     },
#     'specialtiesRequirements': {
#         'specialties': [
#             {
#                 'name': 'Administration',
#                 'year': '5'
#             },
#             {
#                 'name': 'Dialysis',
#                 'year': '3'
#             },
#             {
#                 'name': 'Emergency',
#                 'year': '2'
#             }
#         ],
#         'spokenLanguages': [
#             {
#                 'language': 'English',
#                 'fluency': 'fluent'
#             },
#             {
#                 'language': 'French',
#                 'fluency': 'fluent'
#             },
#             {
#                 'language': 'Hausa',
#                 'fluency': 'fluent'
#             }
#         ],
#         'passedLanguageTest': False,
#         'hasCanadaEvaluatedCredential': True
#     },
#     'IELTSDocument': 'http://res.cloudinary.com/essential-recruit/image/upload/v1667924444/Essentials/documents/ielts/ixxvfjxvapdj7xtmigoo.pdf',
#     'ECADocument': 'http://res.cloudinary.com/essential-recruit/image/upload/v1669363659/Essentials/documents/ecas/ikhvh7efxiykro4rxwmx.pdf',
#     'resumeDocument': 'http://res.cloudinary.com/essential-recruit/image/upload/v1667927678/Essentials/documents/resumes/dunn3jciijwm9b8b2bwb.pdf',
#     'offerLetterDocument': None,
#     'introductoryVideo': 'http://res.cloudinary.com/essential-recruit/video/upload/v1667926060/Essentials/videos/j6f8dzutgk3o7ztgpoo1.mp4',
#     'avatar': 'http://res.cloudinary.com/essential-recruit/image/upload/v1670847905/Essentials/profileImages/wreuwhlwvsjoeyizhob7.jpg',
#     'completedApplicationStages': [
#         {
#             'stageNumber': 6,
#             'stageName': 'Personal Details',
#             'dateCompleted': datetime.datetime(2022, 11, 8, 16, 43, 4, 909000),
#             'dateUpdated': datetime.datetime(2022, 11, 8, 16, 43, 4, 909000),
#             'completed': True
#         },
#         {
#             'stageNumber': 5,
#             'stageName': 'Retention',
#             'dateCompleted': datetime.datetime(2022, 11, 8, 16, 39, 17, 203000),
#             'dateUpdated': datetime.datetime(2022, 11, 8, 16, 39, 17, 203000),
#             'completed': True
#         },
#         {
#             'stageNumber': 4,
#             'stageName': 'Education',
#             'dateCompleted': datetime.datetime(2022, 11, 8, 16, 35, 32, 428000),
#             'dateUpdated': datetime.datetime(2022, 11, 8, 16, 35, 32, 428000),
#             'completed': True
#         },
#         {
#             'stageNumber': 3,
#             'stageName': 'Specialties And Requirements',
#             'dateCompleted': datetime.datetime(2022, 11, 8, 16, 23, 17, 34000),
#             'dateUpdated': datetime.datetime(2022, 11, 8, 16, 23, 17, 34000),
#             'completed': True
#         },
#         {
#             'stageNumber': 2,
#             'stageName': 'Work and Experience',
#             'dateCompleted': datetime.datetime(2022, 11, 8, 16, 6, 21, 328000),
#             'dateUpdated': datetime.datetime(2022, 11, 8, 16, 6, 21, 328000),
#             'completed': True
#         },
#         {
#             'stageNumber': 1,
#             'stageName': 'Location and Preferences',
#             'dateCompleted': datetime.datetime(2022, 11, 8, 15, 36, 40, 520000),
#             'dateUpdated': datetime.datetime(2022, 11, 8, 15, 36, 40, 520000),
#             'completed': True
#         }
#     ],
#     '__v': 0,
#     'currentStage': None,
#     'education': {
#         'highestQualification': 'RN',
#         'certifications': ['NRP', 'OCN'],
#         'otherCertifications': []
#     },
#     'retention': {
#         'workConcern': 'Compensation',
#         'employerSupports': [
#             'Continuing education support',
#             'NCLEX preparation',
#             'Airport pick-up'
#         ]
#     },
#     'phoneNumber': '+23456656556',
#     'documentNames': {
#         'eca': 'css-colors.pdf',
#         'avatar': '2D7AFBB1-CBC7-4918-A0FA-8DE82EC7AC9CL0001.jpeg'
#     },
#     'updatedAt': datetime.datetime(2023, 10, 11, 12, 8, 4, 357000),
#     'isActive': True,
#     'views': 1,
#     'paymentConfirmed': {
#         'licensureSupport': {
#             'date': datetime.datetime(2023, 9, 13, 8, 22, 41),
#             'licenseType': 'premium',
#             'status': 'paid'
#         },
#         'canadaLicensureSupport': {
#             'date': datetime.datetime(2023, 9, 14, 6, 47, 51),
#             'licenseType': 'basic',
#             'status': 'paid'
#         },
#         'canadaImmigrationSupport': {
#             'date': datetime.datetime(2023, 10, 11, 12, 7, 22), 'status': 'paid'
#         }
#     }
# }


# [
#     {
#         '_id': ObjectId('63628cf1fb0e3725b7fd789f'),
#         'email': 'emma234eze@gmail.com',
#         'userVerified': True,
#         'recruiterApproved': False,
#         'role': 'applicant',
#         'createdAt': datetime.datetime(2022, 11, 2, 15, 29, 53, 384000),
#         'updatedAt': datetime.datetime(2023, 10, 11, 13, 6, 0, 872000),
#         '__v': 1,
#         'firstName': 'emmanuel',
#         'lastName': 'eze',
#         'password': '$argon2i$v=19$m=4096,t=3,p=1$5fmkISJf0LMTebKISOr8cg$gH0t+MWPboPQjcRWZJZfYySrTDf4+mMDvJud8qxTAWk',
#         'billingID': 'cus_Od4Rhx8e91op1x',
#         'isUserOnline': False,
#         'notification': {'message': True},
#         'assignedAdmin': 'email check',
#         'isAdminAssigned': True,
#         'availableDays': [],
#         'subscriptionPlan': 'none',
#         'subscriptionStatus': 'none',
#         'verificationCode': 5752,
#         'verificationCodeExpiresIn': datetime.datetime(2023, 9, 11, 15, 4, 22, 833000),
#         'paymentConfirmed': {
#             'licensureSupport': {
#                 'date': datetime.datetime(2023, 9, 13, 8, 22, 41),
#                 'licenseType': 'premium', 'status': 'paid'
#             },
#             'canadaLicensureSupport': {
#                 'date': datetime.datetime(2023, 9, 14, 6, 47, 51),
#                 'licenseType': 'basic',
#                 'status': 'paid'
#             },
#             'canadaImmigrationSupport': {
#                 'date': datetime.datetime(2023, 10, 11, 12, 7, 22),
#                 'status': 'paid'
#             }
#         },
#         'lastLogin': datetime.datetime(2023, 10, 11, 13, 6, 0, 872000)
#     },
# ]
