-- Wave 2 Migration: Add achievements, conversations, exercise_logs tables
-- Run this SQL on your Render PostgreSQL database

-- 1. Achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(50) NOT NULL,
    unlocked_at TIMESTAMP DEFAULT NOW(),
    is_seen BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_achievements_user_id ON achievements(user_id);

-- 2. Conversations table (AI chat memory)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]'::jsonb,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id);

-- 3. Exercise logs table (progressive overload tracking)
CREATE TABLE IF NOT EXISTS exercise_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    exercise_name VARCHAR(200) NOT NULL,
    muscle_group VARCHAR(30),
    sets_data JSONB NOT NULL,
    total_sets INTEGER NOT NULL,
    total_reps INTEGER NOT NULL,
    max_weight_kg NUMERIC(5,1),
    total_volume_kg NUMERIC(8,1),
    notes TEXT,
    workout_plan_id UUID REFERENCES workout_plans(id),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_exercise_logs_user_id ON exercise_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_exercise_logs_exercise_name ON exercise_logs(exercise_name);

-- 4. Meal feedback table (Wave 3)
CREATE TABLE IF NOT EXISTS meal_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
    meal_name VARCHAR(200) NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    rating INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_meal_feedback_user_id ON meal_feedback(user_id);

-- 5. Exercise feedback table (Wave 3)
CREATE TABLE IF NOT EXISTS exercise_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_name VARCHAR(200) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_exercise_feedback_user_id ON exercise_feedback(user_id);

-- 6. Add phone column to users (Wave 3 — WhatsApp bot)
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20) UNIQUE;
CREATE INDEX IF NOT EXISTS ix_users_phone ON users(phone);

-- Done!
-- Verify: SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('achievements', 'conversations', 'exercise_logs', 'meal_feedback', 'exercise_feedback');
