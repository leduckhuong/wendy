class Index {
    index(req, res) {
        res.send('OK');
    }
}

module.exports = new Index();