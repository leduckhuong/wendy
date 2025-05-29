const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const { pool } = require('../config/db');
var auth = require('../libs/auth');

class User {
    create(username, password) {
        return new Promise((resolve, reject) => {
            const query = `INSERT INTO users (username, password) VALUES ('${username}', '${password}')`;
            pool.query(query)
            .then(row => {
                resolve(row);
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
            const query = `SELECT * from users WHERE username='${username}'`;
            pool.query(query)
            .then(row => {
                if (row.rowCount > 0 && bcrypt.compareSync(password, row.rowCount[0].password)) {
                    const refreshToken = jwt.sign({sessionId: null, userId: row.rows[0].id}, auth.jwtRefreshSecret)
                    return this.updateRefreshToken(refreshToken, userAgent)
                }
                else {
                    reject({fn: 'Unauthorized', message: 'Authentication Failed.'});
                }
            })
            .then(row => {
                resolve({token: row.token, refreshToken: row.refreshToken})
            })
            .catch(err => {
                reject(err);
            })
        })
    }

    updateRefreshToken (refreshToken, userAgent) {
        return new Promise((resolve, reject) => {
            var token = ""
            var newRefreshToken = ""
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
            var query = `SELECT * FROM users WHERE id=${userId}`;
            pool.query(query)
            .then(row => {
                if (row && row.enabled !== false) {
                    // Check session exist and sessionId not null (if null then it is a login)
                    if (sessionId !== null) {
                        var sessionExist = row.refreshTokens.findIndex(e => e.sessionId === sessionId && e.token === refreshToken)
                        if (sessionExist === -1) // Not found
                            throw({fn: 'Unauthorized', message: 'Session not found'})
                    }
    
                    // Generate new token
                    var payload = {}
                    payload.id = row._id
                    payload.username = row.username
                    payload.role = row.role
                    payload.firstname = row.firstname
                    payload.lastname = row.lastname
                    payload.email = row.email
                    payload.phone = row.phone
                    payload.roles = auth.acl.getRoles(payload.role)
    
                    token = jwt.sign(payload, auth.jwtSecret, {expiresIn: '15 minutes'})
    
                    // Remove expired sessions
                    row.refreshTokens = row.refreshTokens.filter(e => {
                        try {
                            var decoded = jwt.verify(e.token, auth.jwtRefreshSecret)
                        }
                        catch (err) {
                            var decoded = null
                        }
                        return decoded !== null
                    })
                    // Update or add new refresh token
                    var foundIndex = row.refreshTokens.findIndex(e => e.sessionId === sessionId)
                    if (foundIndex === -1) { // Not found
                        sessionId = generateUUID()
                        newRefreshToken = jwt.sign({sessionId: sessionId, userId: userId}, auth.jwtRefreshSecret, {expiresIn: '7 days'})
                        row.refreshTokens.push({sessionId: sessionId, userAgent: userAgent, token:newRefreshToken})
                     }
                    else {
                        newRefreshToken = jwt.sign({sessionId: sessionId, userId: userId, exp: expiration}, auth.jwtRefreshSecret)
                        row.refreshTokens[foundIndex].token = newRefreshToken
                    }
                    return row.save()
                }
                else if (row) {
                    reject({fn: 'Unauthorized', message: 'Account disabled'})
                }
                else
                    reject({fn: 'NotFound', message: 'Session not found'})
            })
            .then(() => {
                resolve({token: token, refreshToken: newRefreshToken})
            })
            .catch(err => {
                if (err.code === 11000)
                    reject({fn: 'BadParameters', message: 'Username already exists'})
                else
                    reject(err)
            })
        })
    }
}

module.exports = new User();