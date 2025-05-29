const path = require('path');
const fs = require('fs');
const readline = require('readline');

const { pool } = require('../config/db');

const data_path = process.env.DATA_PATH;

const today = new Date();
const yyyy = today.getFullYear();
const mm = String(today.getMonth() + 1).padStart(2, '0');
const dd = String(today.getDate()).padStart(2, '0');

const formatted = `${yyyy}-${mm}-${dd}`;

const file_path = `${path.join(__dirname, data_path)}/${formatted}.txt`;


const insertData = async (text) => {
    const query = `
        INSERT INTO data_v1 (data) VALUES ('${text}');
    `;
    await pool.query(query);
}

const reader = () => {
    return new Promise((resolve, reject) => {
        if (!fs.existsSync(file_path)) {
            return reject({ fn: 'BadParameters', message: 'This file does not exist!' });
        }

        const rl = readline.createInterface({
            input: fs.createReadStream(file_path),
            crlfDelay: Infinity
        });

        rl.on('error', (err) => {
            reject(err);
        });

        (async () => {
            try {
                for await (const line of rl) {
                    await insertData(line);
                }
                resolve("Read file success!");
            } catch (err) {
                reject(err);
            } finally {
                rl.close(); 
            }
        })();
    });
};

module.exports = { reader };
