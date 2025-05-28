const { Pool } = require('pg');

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_DATABASE,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});

const dbDataTable = process.env.DB_DATA_TABLE;

const createTable = async () => {
    const query = `
        CREATE TABLE IF NOT EXISTS ${dbDataTable} (
            id SERIAL PRIMARY KEY,
            data TEXT
        );
    `;
    return pool.query(query);
}

const connect = () => {
    pool.query('SELECT NOW()')
    .then(response => {
        console.log('Connect postgresql success!');
        return createTable();
    })
    .then(response => {
        console.log(`Create ${dbDataTable} table success!`);
    })
    .catch(error => {
        console.log('Error', error);
    })
}

module.exports = { connect, pool };
