from recommendation.utilities.processing import (
    JobRecommender, fetch_data_from_db, prepare_candidate_data,
    preprocess_applications_data, preprocess_certification_data,
    preprocess_job_languages, preprocess_job_specialties, preprocess_jobs_data,
    preprocess_location_preference_data,
    preprocess_specialties_requirement_data, preprocess_users_data,
    preprocess_working_experience_data)

# users_data, applications_data, jobs_data = fetch_data_from_db()

# # Preprocess all data
# users_df = preprocess_users_data(users_data)

# working_experience_processed_df = preprocess_working_experience_data(applications_data)

# location_processed_df = preprocess_location_preference_data(applications_data)

# specialties_requirements_df, specialties_df, languages_df = preprocess_specialties_requirement_data(applications_data)

# certifications_df = preprocess_certification_data(applications_data)

# applications_df = preprocess_applications_data(applications_data)

# jobs_df = preprocess_jobs_data(jobs_data)

# job_processed_df = preprocess_job_specialties(jobs_df, specialties_requirements_df)

# job_processed_df = preprocess_job_languages(job_processed_df, languages_df)

# # Prepare candidate data for recommendation
# candidate_df = prepare_candidate_data(
#     users_df,
#     applications_df,
#     working_experience_processed_df,
#     location_processed_df,
#     specialties_requirements_df,
#     certifications_df,
#     languages_df
# )

# # Compute similarity
# JobRecommender.compute_and_save_similarity(candidate_df, job_processed_df)

# # Instantiate the recommender with the jobs data
# recommender = JobRecommender()

# # To get job recommendations for a specific candidate:
# candidate_index = 0  
# top_n_jobs = recommender.get_job_recommendations(candidate_index, top_n=10)

# # To get candidate recommendations for a specific job:
# job_index = 0  
# top_candidates = recommender.get_top_candidates_for_job(job_index, top_n=10)
