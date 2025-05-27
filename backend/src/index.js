const express = require('express');
const dotenv = require('dotenv');

dotenv.config();

const port = process.env.BACKEND_PORT;

const app = express();

const { connect } = require('./config/db');

const route = require('./routes/index.route');

connect();

route(app);

app.listen(port, () => {
    console.log('Backend listen on port '+port);
})