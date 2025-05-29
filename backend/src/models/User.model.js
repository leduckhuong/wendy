const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const { pool } = require('../config/db');
const auth = require('../libs/auth');
const { generateUUID } = require('../libs/utils');

class User {
    create(username, password) {
        return new Promise((resolve, reject) => {
            var hash = bcrypt.hashSync(password, 10);
            const query = `INSERT INTO users (username, password) VALUES ($1,$2)`;
            pool.query(query, [username, hash])
            .then(rows => {
                resolve(rows);
            })
            .catch(err => {
                reject(err);
            })
        });
    }


    getAll() {
        return new Promise((resolve, reject) => {
            const query = "SELECT * FROM users;"
            pool.query(query)
            .then(rows => {
                resolve(rows)
            })
            .catch(err => {
                reject(err)
            })
        });
    }

    getToken(username, password, userAgent) {
        return new Promise((resolve, reject) => {
            const query = `SELECT * from users WHERE username=$1`;
            pool.query(query, [username])
            .then(rows => {
                if (rows.rowCount > 0 && bcrypt.compareSync(password, rows.rows[0].password)) {
                    const refreshToken = jwt.sign({sessionId: null, userId: rows.rows[0].id}, auth.jwtRefreshSecret)
                    return this.updateRefreshToken(refreshToken, userAgent)
                }
                else {
                    reject({fn: 'Unauthorized', message: 'Authentication Failed.'});
                }
                resolve('OK');
            })
            .then(rows => {
                resolve({token: rows.token, refreshToken: rows.refreshToken})
            })
            .catch(err => {
                reject(err);
            })
        })
    }

    updateRefreshToken (refreshToken, userAgent) {
        return new Promise((resolve, reject) => {
            let token = ""
            let newRefreshToken = ""
            try {
                var decoded = jwt.verify(refreshToken, auth.jwtRefreshSecret)
                var userId = decoded.userId
                var sessionId = decoded.sessionId
                var expiration = decoded.exp
            }
            catch (err) {
                if (err.name === 'TokenExpiredError')
                    reject({fn: 'Unauthorized', message: 'Expired refreshToken'})
                else
                    reject({fn: 'Unauthorized', message: 'Invalid refreshToken'})
            }
            const query = `SELECT id, username FROM users WHERE id = $1`;
            pool.query(query, [userId])
            .then(result1 => {
                if (result1.rowCount > 0) {
                    const query2 = `SELECT * FROM refresh_tokens WHERE user_id = $1`;
                    return pool.query(query2, [userId])
                        .then(result2 => {
                            return { user: result1.rows[0], sessions: result2.rows };
                        });
                } else {
                    reject({ fn: 'Unauthorized', message: 'User not found' });
                }
            })
            .then(({ user, sessions }) => {
                if (sessionId !== null) {
                    const sessionIndex = sessions.findIndex(e => e.session_id === sessionId && e.token === refreshToken);
                    if (sessionIndex === -1) {
                        reject({ fn: 'Unauthorized', message: 'Session not found' });
                    }
                }

                // Generate new access token
                const payload = {
                    userId: user.id,
                    username: user.username
                };
                token = jwt.sign(payload, auth.jwtSecret, { expiresIn: '15 minutes' });

                // Filter expired refresh tokens
                const validSessions = sessions.filter(e => {
                    try {
                        jwt.verify(e.token, auth.jwtRefreshSecret);
                        return true;
                    } catch (err) {
                        return false;
                    }
                });

                if (!sessionId || !validSessions.some(s => s.session_id === sessionId)) {
                    sessionId = generateUUID();
                    newRefreshToken = jwt.sign({ sessionId, userId }, auth.jwtRefreshSecret, { expiresIn: '7 days' });

                    // Insert new session
                    return pool.query(
                        `INSERT INTO refresh_tokens (user_id, session_id, user_agent, token) VALUES ($1, $2, $3, $4)`,
                        [userId, sessionId, userAgent, newRefreshToken]
                    ).then(() => {
                        return { token, refreshToken: newRefreshToken };
                    });
                } else {
                    newRefreshToken = jwt.sign({ sessionId, userId }, auth.jwtRefreshSecret, { expiresIn: '7 days' });

                    // Update token
                    return pool.query(
                        `UPDATE refresh_tokens SET token = $1 WHERE user_id = $2 AND session_id = $3`,
                        [newRefreshToken, userId, sessionId]
                    ).then(() => {
                        return { token, refreshToken: newRefreshToken };
                    });
                }
            })
            .then(() => {
                resolve({token: token, refreshToken: newRefreshToken})
            })
            .catch(err => {
                reject(err)
            })
        })
    }
}

module.exports = new User();