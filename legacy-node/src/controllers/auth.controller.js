const { sendJson } = require('../utils/response');
const { createAuthService } = require('../services/auth.service');

function createAuthController(options = {}) {
  const authService = options.authService || createAuthService(options);

  async function postAdminLogin(req, res, next) {
    try {
      const payload = await authService.loginAdmin(req.body);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function postVisitorLogin(req, res, next) {
    try {
      const payload = await authService.loginVisitorTemp(req.body);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getMe(req, res, next) {
    try {
      const payload = await authService.getCurrentUser(req);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function postLogout(req, res, next) {
    try {
      const payload = await authService.logout(req);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    getMe,
    postAdminLogin,
    postLogout,
    postVisitorLogin,
  };
}

module.exports = {
  createAuthController,
};
