const express = require('express');

const { createAuthController } = require('../controllers/auth.controller');

function createAuthRouter(options = {}) {
  const authController = options.authController
    || createAuthController({ authService: options.authService });

  const authRouter = express.Router();
  authRouter.post('/auth/admin/login', authController.postAdminLogin);
  authRouter.post('/auth/visitor/login', authController.postVisitorLogin);
  authRouter.get('/auth/me', authController.getMe);
  authRouter.post('/auth/logout', authController.postLogout);

  return authRouter;
}

module.exports = {
  createAuthRouter,
};
