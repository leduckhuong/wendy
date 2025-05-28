const express = require('express');
const dotenv = require('dotenv');

dotenv.config();

const port = process.env.BACKEND_PORT || 4141;

const app = express();

const { connect } = require('./config/db');
const { reader } = require('./libs/get_data');

const route = require('./routes/index.route');

connect();

reader();

route(app);

app.listen(port, () => {
    console.log('Backend listen on port '+port);
})