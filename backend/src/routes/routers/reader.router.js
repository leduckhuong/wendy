const router = require('express').Router();

const readerController = require('../../controllers/Reader.controller.js');

router.get('/read', readerController.read);

module.exports = router;