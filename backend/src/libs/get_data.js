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

const dbDataTable = process.env.DB_DATA_TABLE;

const insertData = async (text) => {
    const query = `
        INSERT INTO ${dbDataTable} (data) VALUES ('${text}');
    `;
    await pool.query(query);
}

const reader = async () => {
    try {
        if (!fs.existsSync(file_path)) {
            return
        }
        const rl = readline.createInterface({
            input: fs.createReadStream(file_path),
            crlfDelay: Infinity // Support \r\n và \n
        });

        for await (const line of rl) {
            await insertData(line);
        }

        console.log("Done reading file.");
    } catch (error) {
        console.error("Read file error!");
        console.error(error);
    }
};

module.exports = { reader };
