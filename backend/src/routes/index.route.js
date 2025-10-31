const indexRouter = require('./routers/index.router');
const readerRouter = require('./routers/reader.router');
const userRouter = require('./routers/user.router');
const healthRouter = require('./routers/health.router');

module.exports = function route(app) {
    app.use('/api/user', userRouter);
    app.use('/api/reader', readerRouter);
    app.use('/api/health', healthRouter);
    app.use('/', indexRouter);
}