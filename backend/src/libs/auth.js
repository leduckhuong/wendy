var jwtSecret = process.env.JWT_SECRET;
exports.jwtSecret = jwtSecret

var jwtRefreshSecret = process.env.JWT_REFRESH_SECRET;
exports.jwtRefreshSecret = jwtRefreshSecret

/*  ROLES LOGIC

    role_name: {
        allows: [],
        inherits: []
    }
    allows: allowed permissions to access | use * for all
    inherits: inherits other users "allows"
*/


var builtInRoles = {
    user: {
        allows: [
            
        ]
    },
    admin: {
        allows: "*"
    }
}

try {
    var customRoles = require('../config/roles.json')}
catch(error) {
    var customRoles = []
}
var roles = {...customRoles, ...builtInRoles}

class ACL {
    constructor(roles) {
        if(typeof roles !== 'object') {
            throw new TypeError('Expected an object as input')
        }
        this.roles = roles
    }

    isAllowed(role, permission) {
        // Check if role exists
        if(!this.roles[role] && !this.roles['user']) {
            return false
        }

        let $role = this.roles[role] || this.roles['user'] // Default to user role in case of inexistant role
        // Check if role is allowed with permission
        if ($role.allows && ($role.allows === "*" || $role.allows.indexOf(permission) !== -1 || $role.allows.indexOf(`${permission}-all`) !== -1)) {
            return true
        }

        // Check if there is inheritance
        if(!$role.inherits || $role.inherits.length < 1) {
            return false
        }

        // Recursive check childs until true or false
        return $role.inherits.some(role => this.isAllowed(role, permission))
    }

    hasPermission (permission) {
        var Response = require('./httpResponse')
        var jwt = require('jsonwebtoken')

        return (req, res, next) => {
            if (!req.cookies['token']) {
                Response.Unauthorized(res, 'No token provided')
                return;
            }
            var cookie = req.cookies['token'].split(' ')
            if (cookie.length !== 2 || cookie[0] !== 'JWT') {
                Response.Unauthorized(res, 'Bad token type')
                return
            }
    
            var token = cookie[1]
            jwt.verify(token, jwtSecret, (err, decoded) => {
                if (err) {
                    if (err.name === 'TokenExpiredError')
                        Response.Unauthorized(res, 'Expired token')
                    else
                        Response.Unauthorized(res, 'Invalid token')
                    return
                }
                if ( permission === "validtoken" || this.isAllowed(decoded.role, permission)) {
                    req.decodedToken = decoded
                    return next()
                }
                else {
                    Response.Forbidden(res, 'Insufficient privileges')
                    return
                }
            })
        }
    }

    buildRoles(role) {
        var currentRole = this.roles[role] || this.roles['user'] // Default to user role in case of inexistant role

        var result = currentRole.allows || []

        if (currentRole.inherits) {
            currentRole.inherits.forEach(element => {
                result = [...new Set([...result, ...this.buildRoles(element)])]
            })
        }

        return result
    }

    getRoles(role) {
        var result = this.buildRoles(role)

        if (result.includes('*'))
            return '*'
        
        return result
    }
}

exports.acl = new ACL(roles)