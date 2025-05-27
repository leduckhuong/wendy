const indexRouter = require('./routers/index.router');

module.exports = function route(app) {
    app.use('/', indexRouter);
}