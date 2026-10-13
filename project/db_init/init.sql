-- db_init/init.sql
-- 1. The overall batch run
CREATE TABLE simulation_batches (
    batch_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config_data JSONB NOT NULL
);

-- 2. Each individual parametric variation in that batch
CREATE TABLE simulations (
    simulation_id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES simulation_batches(batch_id) ON DELETE CASCADE,
    idf_filename VARCHAR(255),
    parameters_applied JSONB -- Specific changes made for this run
);

-- 3. The parsed components tied to that specific simulation run
CREATE TABLE idf_components (
    component_id SERIAL PRIMARY KEY,
    simulation_id INT REFERENCES simulations(simulation_id) ON DELETE CASCADE,
    object_type VARCHAR(100),
    object_name VARCHAR(255),
    properties JSONB -- The actual properties *after* parameter changes
);