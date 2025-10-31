const express = require('express');
const router = express.Router();
const healthController = require('../../controllers/Health.controller');

// Health check endpoint
router.get('/', async (req, res) => {
    await healthController.health(req, res);
});

// Detailed metrics endpoint
router.get('/metrics', async (req, res) => {
    await healthController.metrics(req, res);
});

// Readiness probe
router.get('/ready', async (req, res) => {
    const health = await healthController.health(req, res);
    // Readiness is more strict - requires all services to be available
    if (health.status === 'healthy') {
        res.status(200).json({ status: 'ready' });
    } else {
        res.status(503).json({ status: 'not ready' });
    }
});

// Liveness probe
router.get('/live', async (req, res) => {
    // Liveness is less strict - just check if app is running
    res.status(200).json({
        status: 'alive',
        timestamp: new Date().toISOString()
    });
});

module.exports = router;
