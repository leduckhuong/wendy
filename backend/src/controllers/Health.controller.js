const redis = require('redis');
const fs = require('fs').promises;
const path = require('path');

class HealthController {
    constructor() {
        this.redisClient = null;
        this.startTime = Date.now();
        this.stats = {
            uptime: 0,
            redis_connected: false,
            last_redis_check: null,
            files_processed: 0,
            errors: 0
        };
    }

    // Initialize Redis connection
    async initRedis() {
        try {
            this.redisClient = redis.createClient({
                url: process.env.REDIS_URL || 'redis://localhost:6379'
            });

            await this.redisClient.connect();
            this.stats.redis_connected = true;
            this.stats.last_redis_check = new Date().toISOString();
        } catch (error) {
            console.error('Redis connection failed:', error);
            this.stats.redis_connected = false;
        }
    }

    // Health check endpoint
    async health(req, res) {
        try {
            // Update stats
            this.stats.uptime = Math.floor((Date.now() - this.startTime) / 1000);

            // Check Redis connection
            if (this.redisClient) {
                try {
                    await this.redisClient.ping();
                    this.stats.redis_connected = true;
                } catch (error) {
                    this.stats.redis_connected = false;
                }
                this.stats.last_redis_check = new Date().toISOString();
            }

            // Check file system
            const distDir = process.env.DATA_PATH || '../../dist';
            let dist_exists = false;
            let dist_writable = false;

            try {
                await fs.access(distDir);
                dist_exists = true;

                // Test write permission
                const testFile = path.join(distDir, '.health_check');
                await fs.writeFile(testFile, 'test');
                await fs.unlink(testFile);
                dist_writable = true;
            } catch (error) {
                dist_exists = false;
                dist_writable = false;
            }

            const health = {
                status: 'healthy',
                timestamp: new Date().toISOString(),
                uptime_seconds: this.stats.uptime,
                services: {
                    redis: {
                        connected: this.stats.redis_connected,
                        last_check: this.stats.last_redis_check
                    },
                    filesystem: {
                        dist_exists,
                        dist_writable
                    }
                },
                stats: {
                    files_processed: this.stats.files_processed,
                    errors: this.stats.errors
                }
            };

            // Determine overall health
            if (!this.stats.redis_connected || !dist_exists || !dist_writable) {
                health.status = 'unhealthy';
                res.status(503);
            }

            res.json(health);

        } catch (error) {
            console.error('Health check error:', error);
            res.status(500).json({
                status: 'error',
                timestamp: new Date().toISOString(),
                error: error.message
            });
        }
    }

    // Detailed metrics endpoint
    async metrics(req, res) {
        try {
            // Get system info
            const os = require('os');
            const metrics = {
                timestamp: new Date().toISOString(),
                system: {
                    platform: os.platform(),
                    arch: os.arch(),
                    cpus: os.cpus().length,
                    memory: {
                        total: os.totalmem(),
                        free: os.freemem(),
                        used: os.totalmem() - os.freemem()
                    },
                    uptime: os.uptime()
                },
                application: {
                    uptime: Math.floor((Date.now() - this.startTime) / 1000),
                    node_version: process.version,
                    environment: process.env.NODE_ENV || 'development'
                },
                services: {
                    redis: {
                        connected: this.stats.redis_connected,
                        last_check: this.stats.last_redis_check
                    }
                },
                stats: {
                    files_processed: this.stats.files_processed,
                    errors: this.stats.errors
                }
            };

            res.json(metrics);

        } catch (error) {
            console.error('Metrics error:', error);
            res.status(500).json({
                error: 'Failed to get metrics',
                timestamp: new Date().toISOString()
            });
        }
    }

    // Update stats (called by other controllers)
    updateStats(filesProcessed = 0, errors = 0) {
        this.stats.files_processed += filesProcessed;
        this.stats.errors += errors;
    }

    // Cleanup
    async close() {
        if (this.redisClient) {
            await this.redisClient.quit();
        }
    }
}

// Singleton instance
const healthController = new HealthController();

module.exports = healthController;
