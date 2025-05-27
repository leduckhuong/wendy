const { Pool } = require('pg');

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_DATABASE,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});


const connect = () => {
    pool.query('SELECT NOW()')
    .then(response => {
        console.log('Connect postgresql success!');
    })
    .catch(error => {
        console.log('Connect fail!');
        console.log('Error', error);
    })
}
module.exports = { connect };
