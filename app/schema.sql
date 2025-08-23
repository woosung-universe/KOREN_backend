-- ENUM
CREATE TYPE sex_enum AS ENUM ('male', 'female');
CREATE TYPE anatomy_site_enum AS ENUM ('head_neck', 'upper_extremity', 'lower_extremity', 'torso');
CREATE TYPE diagnosis_enum AS ENUM ('benign', 'malignant');

-- PATIENTS
CREATE TABLE patients (
                          id SERIAL PRIMARY KEY,
                          patient_id VARCHAR(255) UNIQUE NOT NULL,
                          name VARCHAR(255) NOT NULL,
                          age INTEGER,
                          sex sex_enum,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MEDICAL_IMAGES
CREATE TABLE medical_images (
                                id SERIAL PRIMARY KEY,
                                image_name VARCHAR(255) UNIQUE NOT NULL,
                                patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                                file_path VARCHAR(255) NOT NULL,
                                anatomy_site anatomy_site_enum,
                                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- COMMUNICATION_SUMMARIES
CREATE TABLE communication_summaries (
                                         id SERIAL PRIMARY KEY,
                                         patient_id INT NOT NULL REFERENCES patients(id),
                                         summary_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                         category TEXT,
                                         content TEXT
);

-- DIAGNOSES
CREATE TABLE diagnoses (
                           id SERIAL PRIMARY KEY,
                           patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
                           medical_image_id INTEGER REFERENCES medical_images(id) ON DELETE CASCADE,
                           communication_summary_id INTEGER REFERENCES communication_summaries(id) ON DELETE SET NULL,
                           diagnosis diagnosis_enum,
                           anatomy_site anatomy_site_enum,
                           confidence_score FLOAT,
                           target_value INTEGER,
                           diagnosed_by VARCHAR(255),
                           ai_description TEXT,
                           diagnosed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);