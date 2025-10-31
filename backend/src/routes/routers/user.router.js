const router = require('express').Router();

const userController = require('../../controllers/User.controller.js');

router.post('/token', userController.token);
router.post('/init', userController.init);
router.get('/verify', userController.verify);

module.exports = router;