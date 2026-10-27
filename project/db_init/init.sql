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
    weather VARCHAR(255),
    status_simulation VARCHAR(100),
    parameters_applied JSONB, -- Specific changes made for this run
    results JSONB
);

-- 3. The parsed components tied to that specific simulation run
CREATE TABLE idf_components (
    component_id SERIAL PRIMARY KEY,
    simulation_id INT REFERENCES simulations(simulation_id) ON DELETE CASCADE,
    type_class VARCHAR(255),
    type_name VARCHAR(255),
    property_name VARCHAR(255),
    property_value VARCHAR(255),
    old_property_value VARCHAR(255),
    weather VARCHAR(255),
    other_properties VARCHAR(255),
    other_values VARCHAR(255)
);
