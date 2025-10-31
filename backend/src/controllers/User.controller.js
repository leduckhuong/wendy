const jwt = require('jsonwebtoken');

const Response = require('../libs/httpResponse');
const passwordpolicy = require('../libs/passwordpolicy');
const UserModel = require('../models/User.model');
const auth = require('../libs/auth');


class User {
    token(req, res) {
        if (!req.body.username || !req.body.password) {
            Response.BadParameters(res, 'Missing some required parameters');
            return;
        }

        if (typeof req.body.password !== "string" || typeof req.body.username !== "string") {
            Response.BadParameters(res, 'Parameters must be of type String');
            return;
        }
        
        UserModel.getToken(req.body.username, req.body.password, req.headers['user-agent'])
        .then(msg => {
            res.cookie('token', `JWT ${msg.token}`, {sameSite: 'strict', secure: true, httpOnly: true})
            res.cookie('refreshToken', msg.refreshToken, {sameSite: 'strict', secure: true, httpOnly: true, path: '/api/users/refreshtoken'})
            return Response.Ok(res, msg)
        })
        .catch(err => Response.Internal(res, err))
    }


    init(req, res) {
        if (!req.body.username || !req.body.password) {
            Response.BadParameters(res, 'Missing some required parameters');
            return;
        }
        if (passwordpolicy.strongPassword(req.body.password)!==true){
            Response.BadParameters(res, 'Password does not match the password policy');
            return;
        }
        const { username, password } = req.body;
        UserModel.getAll()
        .then(users => {
            if(users.rowCount == 0) {
                UserModel.create(username, password)
                .then(msg => {
                    // UserModel.getToken(username, password)
                    // .then(msg => Response.Created(res, msg))
                    // .catch(err => Response.Internal(res, err))
                    console.log(msg);
                    return res.send("OK");
                })
                .catch(err => Response.Internal(err, msg))
            }
            else {
                return Response.Forbidden(res, 'Already Initialized');
            }
        })
        .catch(err => Response.Internal(res, err))
    }

    verify(req, res) {
        if (!req.cookies['token']) {
            return Response.Unauthorized(res, 'No token provided');
        }

        const cookie = req.cookies['token'].split(' ');
        if (cookie.length !== 2 || cookie[0] !== 'JWT') {
            return Response.Unauthorized(res, 'Bad token type');
        }

        const token = cookie[1];
        jwt.verify(token, auth.jwtSecret, (err, decoded) => {
            if (err) {
                if (err.name === 'TokenExpiredError') {
                    return Response.Unauthorized(res, 'Expired token');
                } else {
                    return Response.Unauthorized(res, 'Invalid token');
                }
            }
            return Response.Ok(res, { user: decoded });
        });
    }
}

module.exports = new User();