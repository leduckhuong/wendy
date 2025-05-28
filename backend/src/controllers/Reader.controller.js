const { reader } = require('../libs/get_data');
const Response = require('../libs/httpResponse');

class Reader {
    index(req, res) {
        const msg = "Ok";
        return Response.Ok(res, msg);
    }
    async read(req, res) {
        reader()
        .then(msg => Response.Ok(res, msg))
        .catch(err => Response.Internal(res, err))
    }
}

module.exports = new Reader();