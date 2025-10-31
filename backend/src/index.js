const express = require('express');
const dotenv = require('dotenv');

dotenv.config();

const port = process.env.BACKEND_PORT || 4141;

const app = express();

const { connect } = require('./config/db');
const healthController = require('./controllers/Health.controller');

const route = require('./routes/index.route');

// Initialize database connection
connect();

// Initialize health controller
(async () => {
    await healthController.initRedis();
})();

// Middleware
app.use(express.json());
app.use(express.urlencoded({extended: true}));

// Routes
route(app);

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...');
    await healthController.close();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    await healthController.close();
    process.exit(0);
});

app.listen(port, () => {
    console.log(`Backend listening on port ${port}`);
    console.log(`Health check available at http://localhost:${port}/api/health`);
});