const indexRouter = require('./routers/index.router');
const readerRouter = require('./routers/reader.router');

module.exports = function route(app) {
    app.use('/reader', readerRouter);
    app.use('/', indexRouter);
}