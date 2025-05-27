const router = require('express').Router();

const indexController = require('../../controllers/Index.controller');

router.get('/', indexController.index);

module.exports = router;