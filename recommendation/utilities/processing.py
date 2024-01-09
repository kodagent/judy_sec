import itertools

import numpy as np
import pandas as pd
from bson import ObjectId
from sklearn.metrics.pairwise import cosine_similarity

from chatbackend.configs.logging_config import configure_logger
from optimizers.mg_database import db
from recommendation.models import SimilarityMatrix

logger = configure_logger(__name__)

MAX_YEARS = 10
FALLBACK_YEARS = 2

# Constants for features
FEATURES_FOR_USERS = ["_id", "role", "userVerified", "recruiterApproved", "availableDays", "subscriptionPlan", "subscriptionStatus", "lastLogin"]
FEATURES_FOR_APPLICATIONS = ["owner"]
FEATURES_FOR_WORKING_EXPERIENCE = ["yearOfExperience", "hasLicense", "processingCanadaLicense", "locationsOfActiveLicense"]
FEATURES_FOR_LOCATION_PREFERENCES = ["currentLocation", "interestedProvince", "interestedCityInSelectedProvince"]
FEATURES_FOR_JOBS = ["_id", "title", "experienceYears", "jobType", "specialties", "otherSpecialties", "location", "requiredLanguage", "salaryRange", "benefits", "relocation", "status"]

def fetch_data_from_db():
    """Fetch data from the given database.

    Args:
    - database (object): The database object to fetch data from.

    Returns:
    - tuple: A tuple containing users_data, applications_data, and jobs_data.
    """

    users_data = list(db['users'].find({}))
    applications_data = list(db['applications'].find({}))
    immigrations_data = list(db['immigrations'].find({}))
    jobs_data = list(db['jobs'].find({}))

    return users_data, applications_data, jobs_data

def preprocess_users_data(users_data):
    """Preprocess users data.

    Args:
    - users_data (list): List of user data dictionaries.

    Returns:
    - DataFrame: A preprocessed DataFrame of user data.
    """

    # Assume "features_for_users" and "features_for_jobs" are lists of feature column names you want to consider for users and jobs respectively
    users_df = pd.DataFrame(users_data)[FEATURES_FOR_USERS]
    users_df = users_df.rename(columns={'_id': 'UserID'})

    # User df Preprocessing
    # Filter the DataFrame to keep only 'applicant' users
    users_df = users_df[users_df['role'] == 'applicant']

    users_df['recruiterApproved'] = users_df['recruiterApproved'].fillna(False)

    # Convert NaN to empty list
    users_df['availableDays'] = users_df['availableDays'].apply(lambda x: [] if isinstance(x, float) and pd.isnull(x) else x)

    # Convert lists of days into a single string representation
    users_df['availableDays'] = users_df['availableDays'].apply(lambda x: ','.join(x))

    # One-hot encode days of the week
    availability_dummies = users_df['availableDays'].str.get_dummies(sep=',')
    users_df = pd.concat([users_df, availability_dummies], axis=1)

    users_df['subscriptionPlan'] = users_df['subscriptionPlan'].fillna('none')
    users_df['subscriptionStatus'] = users_df['subscriptionStatus'].fillna('none')

    users_df['lastLogin'] = pd.to_datetime(users_df['lastLogin']).dt.strftime('%Y-%m-%d')  # Convert to just date, for simplicity

    # Convert boolean columns to integers
    bool_cols = ['userVerified', 'recruiterApproved']
    for col in bool_cols:
        users_df[col] = users_df[col].astype(int)

    # Drop columns that don't provide variability or useful information
    columns_to_drop = ['role', 'availableDays', 'subscriptionPlan', 'subscriptionStatus']
    users_df = users_df.drop(columns=columns_to_drop)

    # Drop lastLogin column
    users_df.drop('lastLogin', axis=1, inplace=True)

    return users_df

def preprocess_working_experience_data(applications_data):
    # Working Experience df Preprocessing
    # Extract the desired fields and create a DataFrame
    working_experience_df = pd.DataFrame([{**{'UserID': app['owner']}, **{feature: app.get("workingExperience", {}).get(feature) for feature in FEATURES_FOR_WORKING_EXPERIENCE}} for app in applications_data])

    # Extract numeric values from 'yearOfExperience' and handle cases without "year(s)"
    working_experience_df['yearOfExperience'] = working_experience_df['yearOfExperience'].apply(
        lambda x: float(x.split()[0]) if isinstance(x, str) and 'year(s)' in x else float(x) if str(x).isdigit() else None
    )

    # Fill missing values with 0 or any other appropriate value
    working_experience_df['yearOfExperience'].fillna(0, inplace=True)

    # Convert boolean columns to numeric
    working_experience_df['hasLicense'] = working_experience_df['hasLicense'].astype(int)
    working_experience_df['processingCanadaLicense'] = working_experience_df['processingCanadaLicense'].astype(int)

    # Flatten the 'locationsOfActiveLicense' column
    # Extract the number of active licenses
    working_experience_df['numActiveLicenses'] = working_experience_df['locationsOfActiveLicense'].apply(len)

    # Extract the list of countries with active licenses, considering potential missing or inconsistent data
    working_experience_df['activeLicenseCountries'] = working_experience_df['locationsOfActiveLicense'].apply(
        lambda x: [item['location'] for item in x if 'location' in item]
    )

    # Drop the original 'locationsOfActiveLicense' column
    working_experience_df.drop(columns=['locationsOfActiveLicense'], inplace=True)

    activeLicenseCountries_dummies = working_experience_df['activeLicenseCountries'].str.join('|').str.get_dummies()
    activeLicenseCountries_dummies.columns = ['activeLicenseCountries_' + col for col in activeLicenseCountries_dummies.columns]
    activeLicenseCountries_dummies['UserID'] = working_experience_df['UserID'].values

    threshold = 0.05  # 5%

    # Compute the mean and std only for columns that exclude 'UserID'
    numeric_columns = activeLicenseCountries_dummies.drop(columns='UserID')
    cols_to_drop = numeric_columns.columns[
        (numeric_columns.mean() < threshold) |
        (numeric_columns.std() < threshold)
    ]

    activeLicenseCountries_dummies.drop(columns=cols_to_drop, inplace=True)
    
    # Drop the original 'activeLicenseCountries' column
    working_experience_df.drop(columns=['activeLicenseCountries'], inplace=True)

    working_experience_processed_df = pd.merge(working_experience_df, activeLicenseCountries_dummies, on='UserID', how='left')

    return working_experience_processed_df

def preprocess_location_preference_data(applications_data):
    # Location Preferences df Preprocessing
    # Extract the desired fields and create a DataFrame
    location_preferences_df = pd.DataFrame([{**{'UserID': app['owner']}, **{feature: app.get("locationPreferences", {}).get(feature) for feature in FEATURES_FOR_LOCATION_PREFERENCES}} for app in applications_data])

    location_preferences_df['interestedCityInSelectedProvince'] = location_preferences_df['interestedCityInSelectedProvince'].replace('Airdries', 'Airdrie')

    # Fill missing values with 'Unknown' or any other strategy you decide on
    location_preferences_df.fillna('Unknown', inplace=True)

    # Calculate popularity scores
    current_location_popularity = location_preferences_df['currentLocation'].value_counts(normalize=True)
    interested_province_popularity = location_preferences_df['interestedProvince'].value_counts(normalize=True)
    interested_city_popularity = location_preferences_df['interestedCityInSelectedProvince'].value_counts(normalize=True)

    # Map the popularity scores to your main dataframe
    location_preferences_df['currentLocation_popularity_score'] = location_preferences_df['currentLocation'].map(current_location_popularity)
    location_preferences_df['interestedProvince_popularity_score'] = location_preferences_df['interestedProvince'].map(interested_province_popularity)
    location_preferences_df['interestedCity_popularity_score'] = location_preferences_df['interestedCityInSelectedProvince'].map(interested_city_popularity)

    # One-hot encode the 'currentLocation' column
    current_location_dummies = pd.get_dummies(location_preferences_df['currentLocation'], prefix='currentLocation')

    # One-hot encode the 'interestedProvince' column
    interested_province_dummies = pd.get_dummies(location_preferences_df['interestedProvince'], prefix='interestedProvince')

    # # If we decide to keep city granularity
    # interested_city_dummies = pd.get_dummies(location_preferences_df['interestedCityInSelectedProvince'], prefix='interestedCity')

    # Concatenate the original data frame with the dummy dataframes
    location_processed_df = pd.concat([location_preferences_df, current_location_dummies, interested_province_dummies], axis=1)  # , interested_city_dummies], axis=1)

    # Drop the original categorical columns
    location_processed_df.drop(columns=['currentLocation', 'interestedProvince', 'interestedCityInSelectedProvince'], inplace=True)

    return location_processed_df

def preprocess_specialties_requirement_data(applications_data):
    # specialtiesRequirements df Preprocessing
    # Filter applications based on the presence of specialtiesRequirements or spokenLanguages
    specialities_data = []
    spoken_languages_data = []
    additional_data = []  # for passedLanguageTest and hasCanadaEvaluatedCredential

    for app in applications_data:
        app_id = app.get('owner')

        specialties = app.get("specialtiesRequirements", {}).get("specialties", [])
        spoken_languages = app.get("specialtiesRequirements", {}).get("spokenLanguages", [])
        passed_test = app.get("specialtiesRequirements", {}).get("passedLanguageTest", False)
        canada_cred = app.get("specialtiesRequirements", {}).get("hasCanadaEvaluatedCredential", False)

        if specialties or spoken_languages:
            additional_data.append({
                "UserID": app_id,
                "passedLanguageTest": passed_test,
                "hasCanadaEvaluatedCredential": canada_cred
            })

        if specialties:
            specialities_data.append({
                "UserID": app_id,
                "specialties": specialties
            })

        if spoken_languages:
            spoken_languages_data.append({
                "UserID": app_id,
                "spokenLanguages": spoken_languages
            })

    # Convert specialties data to DataFrame
    specialties_list = [item['specialties'] for item in specialities_data]
    ids = [item['UserID'] for item in specialities_data]

    specialties_df = pd.DataFrame(ids, columns=['UserID'])
    for i, specialties in enumerate(specialties_list):
        for specialty in specialties:
            specialty_name = "specialties_" + specialty['name']
            specialty_year = int(specialty['year'])
            specialties_df.loc[i, specialty_name] = specialty_year

    specialties_df = specialties_df.fillna(0)

    specialties_df[specialties_df.columns[1:]] = specialties_df[specialties_df.columns[1:]].clip(upper=MAX_YEARS)

    popularity_scores = (specialties_df.iloc[:, 1:] > 0).sum() / len(specialties_df)
    specialties_df['max_popularity_score'] = specialties_df.iloc[:, 1:].apply(lambda row: max(row * popularity_scores), axis=1)

    # Convert spoken languages data to DataFrame
    languages_list = [item['spokenLanguages'] for item in spoken_languages_data]
    ids = [item['UserID'] for item in spoken_languages_data]

    languages_df = pd.DataFrame(ids, columns=['UserID'])
    for i, languages in enumerate(languages_list):
        for lang in languages:
            language_name = lang['language']
            language_fluency = lang['fluency']
            if language_name not in languages_df.columns:
                languages_df[language_name] = np.nan
                languages_df[language_name] = languages_df[language_name].astype('object')
            languages_df.at[i, language_name] = language_fluency

    languages_df = languages_df.fillna("None")

    # Mapping string fluency levels to numerical values
    fluency_mapping = {
        'None': 0,
        'Basic': 1,
        'Intermediate': 2,
        'Fluent': 3
    }

    for column in languages_df.columns:
        if column != 'UserID':
            languages_df[column] = languages_df[column].map(fluency_mapping).fillna(0).astype(int)

    # List of columns excluding the 'UserID' column
    language_cols = languages_df.columns[1:]

    # Identify columns to group into "Others"
    cols_to_group = [col for col in language_cols if languages_df[col].max() <= 1]

    # Create "Others" column which is the sum of the columns identified to group
    languages_df['OthersLanguages'] = languages_df[cols_to_group].sum(axis=1)

    # Drop the columns that were grouped
    languages_df.drop(columns=cols_to_group, inplace=True)

    # Convert additional data to DataFrame
    additional_df = pd.DataFrame(additional_data)

    # Replace None values with False for the specific columns
    additional_df["passedLanguageTest"].fillna(False, inplace=True)
    additional_df["hasCanadaEvaluatedCredential"].fillna(False, inplace=True)

    # Convert boolean values to integers
    additional_df["passedLanguageTest"] = additional_df["passedLanguageTest"].astype(int)
    additional_df["hasCanadaEvaluatedCredential"] = additional_df["hasCanadaEvaluatedCredential"].astype(int)

    # Merge DataFrames to create specialties_requirements_df
    specialties_requirements_df = specialties_df.merge(languages_df, how='inner', on='UserID').merge(additional_df, how='inner', on='UserID')
    
    return specialties_requirements_df, specialties_df, languages_df

def preprocess_certification_data(applications_data):
    # Define a mapping of certifications
    certification_mapping = {
        "NRP": "Neonatal Resuscitation Program",
        "OCN": "Oncology Certified Nurse",
        "ACLS": "Advanced Cardiac Life Support",
        "CPR": "Cardiopulmonary Resuscitation",
        "ONS": "Oncology Nursing Society",
        "PALS": "Pediatric Advanced Life Support",
        "BLS": "Basic Life Support",
        # Add more mappings as needed
    }

    # Filter applications based on the presence of "education" and "certifications" data
    filtered_applications_data = [app for app in applications_data if app.get("education") and app["education"].get("certifications")]

    # Initialize an empty dictionary to store certification data
    certification_data = {}

    # Initialize an empty list to store UserIDs for certifications
    user_ids_cert = []

    # Iterate through filtered applications
    for i, app in enumerate(filtered_applications_data):
        certifications = app["education"]["certifications"]

        # Initialize a dictionary to store binary values for each certification
        cert_values = {cert: False for cert in certification_mapping}

        # Append the UserID to the list
        user_ids_cert.append(app['owner'])

        # Set the value to True for the certifications the applicant has
        for cert in certifications:
            full_cert_name = certification_mapping.get(cert)
            if full_cert_name:
                cert_values[full_cert_name] = True

        # Append certification data to the dictionary
        certification_data[i] = cert_values

    # Create a DataFrame from the dictionary
    certifications_df = pd.DataFrame.from_dict(certification_data, orient='index')

    # Add the 'UserID' column to the certifications_df
    certifications_df['UserID'] = user_ids_cert

    # Reorder columns to match the desired order
    certifications_df = certifications_df[
        [
            'UserID', "Neonatal Resuscitation Program", "Oncology Certified Nurse",
            "Advanced Cardiac Life Support", "Cardiopulmonary Resuscitation",
            "Oncology Nursing Society", "Pediatric Advanced Life Support",
            "Basic Life Support"
        ]
    ]

    # Fill NaN values with 0
    certifications_df.fillna(0, inplace=True)

    # Convert boolean columns to integer (True to 1, False to 0)
    for col in certification_mapping.values():
        certifications_df[col] = certifications_df[col].astype(int)
    
    return certifications_df

def preprocess_applications_data(applications_data):
    applications_df = pd.DataFrame(applications_data)[FEATURES_FOR_APPLICATIONS]
    applications_df = applications_df.rename(columns={'owner': 'UserID'})

    return applications_df

def preprocess_jobs_data(jobs_data):
    jobs_df = pd.DataFrame(jobs_data)[FEATURES_FOR_JOBS]
    
    # Handle missing values
    jobs_df['title'].fillna('Unknown', inplace=True)
    # Normalize Text Data
    jobs_df['title'] = jobs_df['title'].str.lower().str.replace('[^a-z\s]', '')

    jobs_df = jobs_df.rename(columns={'experienceYears': 'yearOfExperience'})
    jobs_df['yearOfExperience'] = jobs_df['yearOfExperience'].fillna(2.0)
    
    return jobs_df

def process_specialties(row):
    merged_specialties = {}
    
    # Start with the 'specialties' column
    for item in row['specialties']:
        if 'specialty' in item:
            merged_specialties[item['specialty']] = item.get('yearsOfExperience', FALLBACK_YEARS)
    
    # Process 'otherSpecialties' - only add those that aren't already in the merged dictionary
    for item in row['otherSpecialties']:
        if 'specialty' in item and item['specialty'] not in merged_specialties:
            merged_specialties[item['specialty']] = item.get('yearsOfExperience', FALLBACK_YEARS)
    
    return merged_specialties

def preprocess_job_specialties(jobs_df, specialties_requirements_df):
    # Apply the merge function to each row and create 'all_specialties' column
    jobs_df['all_specialties'] = jobs_df.apply(process_specialties, axis=1)

    # Separate the merged specialties into two new columns
    jobs_df['specialty_list'] = jobs_df['all_specialties'].apply(lambda x: list(x.keys()))
    jobs_df['specialty_years'] = jobs_df['all_specialties'].apply(lambda x: list(x.values()))

    # Optional: Drop the 'all_specialties' column after extraction
    jobs_df.drop(columns=['all_specialties'], inplace=True)

    # Assuming you have already processed jobs_df to get 'specialty_list' and 'specialty_years' columns.

    # Convert the 'specialty_list' and 'specialty_years' columns into a dictionary with specialties as keys and years as values
    jobs_df['specialties_dict'] = jobs_df.apply(lambda row: dict(zip(row['specialty_list'], row['specialty_years'])), axis=1)

    # Extract all unique specialties from jobs_df
    all_specialties_in_jobs = set(itertools.chain(*jobs_df['specialties_dict'].tolist()))

    # Columns in specialties_requirements_df that correspond to specialties
    specialty_cols = specialties_requirements_df.columns[1:-9].tolist()  # assuming 'UserID' is the first column and the last 9 columns are the non-specialty columns

    # Check if there are specialties in jobs_df that are not in specialties_requirements_df
    unhandled_specialties = all_specialties_in_jobs - set(specialty_cols)

    if unhandled_specialties:
        logger.info(f"Warning: The following specialties are present in the jobs data but not in specialties_requirements_df: {', '.join(unhandled_specialties)}")

    # For the specialties that are present in specialties_requirements_df, create separate columns with years as values
    for specialty in specialty_cols:
        if 'specialties_' + specialty not in jobs_df.columns:  # Check if the column does not exist already
            jobs_df['specialties_' + specialty] = jobs_df['specialties_dict'].apply(lambda x: x.get(specialty, 0))

    # Convert the dictionary in 'specialties_dict' column into separate columns
    # expanded_specialties = jobs_df['specialties_dict'].apply(pd.Series, dtype='float64')
    expanded_specialties = pd.DataFrame(jobs_df['specialties_dict'].tolist()).astype('float64')

    # Handle NaN values by filling them with 0
    expanded_specialties = expanded_specialties.fillna(0)

    # Add a prefix 'specialities_' to each of these columns
    expanded_specialties = expanded_specialties.add_prefix('specialties_')

    # Join these new columns back to the original dataframe
    job_processed_df = pd.concat([jobs_df, expanded_specialties], axis=1)

    # Drop columns used for the transformation
    job_processed_df.drop(columns=['specialties', 'otherSpecialties', 'specialty_list', 'specialty_years', 'specialties_dict'], inplace=True)

    return job_processed_df

def preprocess_job_languages(jobs_df, languages_df):
    # Mapping string fluency levels to numerical values
    fluency_mapping = {
        'None': 0,
        'none': 0,
        'Basic': 1,
        'basic': 1,
        'Intermediate': 2,
        'intermediate': 2,
        'Fluent': 3,
        'fluent': 3
    }

    # Create dictionary columns for languages and their fluency
    jobs_df['languages_dict'] = jobs_df['requiredLanguage'].apply(lambda x: {item['language']: fluency_mapping[item['fluency']] for item in x})

    # Create separate columns for each language with fluency level as values
    for language in languages_df.columns[1:]:  # excluding 'UserID'
        jobs_df[language] = jobs_df['languages_dict'].apply(lambda x: x.get(language, 0))

    jobs_df.drop(columns=['requiredLanguage'], inplace=True)

    # Calculate 'OthersLanguages' column
    known_languages = languages_df.columns[1:].tolist()
    jobs_df['OthersLanguages'] = jobs_df['languages_dict'].apply(lambda x: sum(value for key, value in x.items() if key not in known_languages))

    jobs_df.drop(columns=['languages_dict'], inplace=True)

    jobs_df['location'].fillna('Unknown', inplace=True)
    job_location_dummies = pd.get_dummies(jobs_df['location'], prefix='interestedProvince')

    jobs_df['relocation'].fillna(False, inplace=True)
    # Add relocation binary column
    jobs_df['relocation_available'] = jobs_df['relocation'].astype(int)

    # Concatenate the original data frame with the dummy dataframe
    job_processed_df = pd.concat([jobs_df, job_location_dummies], axis=1)

    # Drop the original categorical columns and other columns not needed for similarity calculation
    columns_to_drop = ['title', 'jobType', 'salaryRange', 'benefits', 'location', 'relocation', 'status']

    job_processed_df.drop(columns=columns_to_drop, inplace=True)

    return job_processed_df

def prepare_candidate_data(users_df, applications_df, working_experience_processed_df, location_processed_df, specialties_requirements_df, certifications_df, languages_df):
    _df = working_experience_processed_df.merge(location_processed_df, how='inner', on='UserID')
    _df = _df.merge(specialties_requirements_df, how='inner', on='UserID')
    _df = _df.merge(certifications_df, how='inner', on='UserID')
    applications_df = applications_df.merge(_df, how='inner', on='UserID')
    candidate_df = users_df.merge(applications_df, how='inner', on='UserID')

    return candidate_df


class JobRecommender:
    @staticmethod
    def compute_and_save_similarity(candidate_df, jobs_df):
        # Compute common columns without "_id"
        common_columns = candidate_df.columns.intersection(jobs_df.columns)
        candidates_for_similarity = candidate_df[common_columns].copy()
        jobs_for_similarity = jobs_df[common_columns].copy()
        
        # Compute the cosine similarity matrix
        similarity_matrix = cosine_similarity(jobs_for_similarity, candidates_for_similarity)
        job_ids = jobs_df['_id'].tolist()
        candidate_ids = candidate_df['UserID'].tolist()

        # Save the similarity matrix and job IDs
        similarity_instance = SimilarityMatrix()
        # Ensure that the `set_matrix` function is being called with the correct arguments
        similarity_instance.set_matrix(similarity_matrix, job_ids, candidate_ids)

    def load_similarity_matrix(self):
        latest_similarity = SimilarityMatrix.objects.latest('date_created')
        matrix = latest_similarity.get_matrix()
        return matrix

    def load_job_ids(self):
        latest_similarity = SimilarityMatrix.objects.latest('date_created')
        job_ids = latest_similarity.get_job_ids()
        return job_ids
    
    def load_candidate_ids(self):
        latest_similarity = SimilarityMatrix.objects.latest('date_created')
        candidate_ids = latest_similarity.get_candidate_ids()
        return candidate_ids
    
    def get_index_from_job_id(self, job_id):
        job_ids = self.load_job_ids()
        logger.info(f"These are the job ids in the database: \n{job_ids}")
        return job_ids.index(job_id)

    def get_index_from_candidate_id(self, candidate_id):
        candidate_ids = self.load_candidate_ids()
        logger.info(f"These are the candidate ids in the database: \n {candidate_ids}")
        return candidate_ids.index(candidate_id)

    def get_job_recommendations_by_id(self, candidate_id, top_n=10):
        candidate_index = self.get_index_from_candidate_id(candidate_id)
        return self.get_job_recommendations(candidate_index, top_n)

    def get_top_candidates_for_job_by_id(self, job_id, top_n=10):
        job_index = self.get_index_from_job_id(job_id)
        return self.get_top_candidates_for_job(job_index, top_n)
    
    def get_job_recommendations(self, candidate_index, top_n=10):
        # Load the similarity matrix and job IDs
        similarity_matrix = self.load_similarity_matrix()
        job_ids = self.load_job_ids()
        
        # Fetch similarity scores for the candidate
        candidate_scores = similarity_matrix[:, candidate_index]
        
        # Get the indices of the top N jobs for this candidate based on their scores
        top_jobs_indices = np.argsort(candidate_scores)[-top_n:][::-1]
        
        # Map the top job indices to job IDs
        top_job_ids = [job_ids[index] for index in top_jobs_indices]

        # Get the similarity scores of these top jobs
        top_jobs_scores = candidate_scores[top_jobs_indices]

        # Fetch additional job details from MongoDB
        jobs = db['jobs'].find({'_id': {'$in': [ObjectId(job_id) for job_id in top_job_ids]}})

        # Extract the required fields from the job documents
        job_details_with_scores = []
        for job in jobs:
            job_id = str(job['_id'])  
            job_details_with_scores.append(
                {
                    'score': top_jobs_scores[top_job_ids.index(job_id)],
                    'city': job.get('city'),
                    'location': job.get('location'),
                    'id': job_id,
                    'owner': str(job.get('owner')),
                    'title': job.get('title'),
                    'slug': job.get('slug'),
                    'job_type': job.get('jobType'),
                    'salary_range': job.get('salaryRange'),
                    'experience_years': job.get('experienceYears'),
                    'company_name': job.get('companyName'),
                    'company_logo': job.get('companyLogo')
                }
            )

        return job_details_with_scores

    def get_top_candidates_for_job(self, job_index, top_n=10):
        """
        Get top n candidates for a specific job based on its index.
        
        Args:
            job_index (int): Index of the job.
            top_n (int): Number of top candidates to retrieve. Default is 10.

        Returns:
            dict: Dictionary with candidate IDs as keys and their similarity scores as values.
        """
        
        similarity_matrix = self.load_similarity_matrix()

        # Load the candidate IDs
        candidate_ids = self.load_candidate_ids()

        # Fetch the similarity scores for the specified job
        job_scores = similarity_matrix[job_index]
        
        # Get the indices of the top N candidates for this job based on their scores
        top_candidates_indices = np.argsort(job_scores)[-top_n:][::-1]
        
        # Map the top candidate indices to candidate IDs
        top_candidate_ids = [candidate_ids[index] for index in top_candidates_indices]

        # Get the similarity scores of these top candidates
        top_candidates_scores = job_scores[top_candidates_indices]
        
        # Create a dictionary with candidate IDs as keys and their similarity scores as values
        top_candidates_for_job = {str(candidate_id): score for candidate_id, score in zip(top_candidate_ids, top_candidates_scores)}

        return top_candidates_for_job

    # def precision_at_k(recommended_items, relevant_items, k):
    #     # Get top-k recommended items
    #     top_k = recommended_items[:k]
    #     relevant_count = sum([1 for item in top_k if item in relevant_items])
    #     return relevant_count / k

    # def recall_at_k(recommended_items, relevant_items, k):
    #     top_k = recommended_items[:k]
    #     relevant_count = sum([1 for item in top_k if item in relevant_items])
    #     return relevant_count / len(relevant_items)

    # # Usage:
    # # recommended_jobs = [list of job ids recommended by the system]
    # # applied_jobs = [list of job ids the candidate actually applied to]
    # precision_score = precision_at_k(recommended_jobs, applied_jobs, k=10)
    # recall_score = recall_at_k(recommended_jobs, applied_jobs, k=10)