const Response = require('../libs/httpResponse');

class Index {
    index(req, res) {
        const msg = "Ok";
        return Response.Ok(res, msg);
    }
}

module.exports = new Index();