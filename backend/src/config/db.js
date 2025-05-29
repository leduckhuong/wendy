const { Pool } = require('pg');

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_DATABASE,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});

const createTableQueries = [
    `CREATE TABLE IF NOT EXISTS data_v1 (
        id SERIAL PRIMARY KEY,
        username TEXT,
        password TEXT,
        refreshTokens TEXT
    );`,
    `CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );`,
    `CREATE TABLE IF NOT EXISTS refresh_tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        session_id TEXT,
        user_agent TEXT,
        token TEXT
    );`
];


const connect = async () => {
    try {
        const res = await pool.query('SELECT NOW()');
        console.log('Connect PostgreSQL success!', res.rows[0].now);

        await Promise.all(createTableQueries.map(query => pool.query(query)));
        console.log('All tables created or verified successfully!');
    } catch (err) {
        console.error('Database connection or table creation error:', err);
    }
};

module.exports = { connect, pool };
