const indexRouter = require('./routers/index.router');
const readerRouter = require('./routers/reader.router');
const userRouter = require('./routers/user.router');

module.exports = function route(app) {
    app.use('/api/user', userRouter);
    app.use('/api/reader', readerRouter);
    app.use('/', indexRouter);
}