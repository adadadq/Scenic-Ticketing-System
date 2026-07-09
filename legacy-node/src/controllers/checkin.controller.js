const { sendJson } = require('../utils/response');
const { createCheckinService } = require('../services/checkin.service');

function createCheckinController(options = {}) {
  const checkinService = options.checkinService || createCheckinService(options);

  async function postCheckin(req, res, next) {
    try {
      const payload = await checkinService.performCheckin(req.body);
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    postCheckin,
  };
}

module.exports = {
  createCheckinController,
};
