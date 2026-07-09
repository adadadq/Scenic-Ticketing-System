const crypto = require('node:crypto');
const { AppError } = require('../utils/app-error');
const { isNonEmptyString } = require('../utils/validators');
const { createAuthQuery } = require('../db/queries/auth.query');
const { createVisitorQuery } = require('../db/queries/visitor.query');

function normalizePhoneKey(value) {
  return String(value || '').trim();
}

function buildVisitorSessionVisitor(visitor, scope) {
  return {
    role: 'VISITOR',
    scope,
    id: Number(visitor.id),
    visitorId: Number(visitor.id),
    displayName: visitor.visitorName,
    visitorName: visitor.visitorName,
    phone: visitor.phone || null,
    idType: visitor.idType,
    idNumber: visitor.idNumber,
    gender: visitor.gender || null,
    birthDate: visitor.birthDate || null,
  };
}

function buildAdminSessionUser(admin) {
  return {
    role: 'ADMIN',
    scope: 'ADMIN',
    id: Number(admin.id),
    username: admin.username,
    displayName: admin.displayName,
    phone: admin.phone || null,
  };
}

function constantTimeEqual(a, b) {
  const left = Buffer.from(String(a || ''));
  const right = Buffer.from(String(b || ''));

  if (left.length !== right.length) {
    return false;
  }

  return crypto.timingSafeEqual(left, right);
}

function verifyDemoHashPassword(password, passwordHash) {
  const demoHash = '$2b$12$example_hash_value_for_demo_only';
  if (passwordHash !== demoHash) {
    return false;
  }

  const demoOnlyPasswords = [
    'LEGACY_DEMO_PASSWORD_A_DO_NOT_USE',
    'LEGACY_DEMO_PASSWORD_B_DO_NOT_USE',
    'LEGACY_DEMO_PASSWORD_C_DO_NOT_USE',
  ];

  return demoOnlyPasswords.some((candidate) => constantTimeEqual(password, candidate));
}

function verifyAdminPassword(password, passwordHash) {
  const normalizedHash = String(passwordHash || '');
  if (!normalizedHash) {
    return false;
  }

  if (verifyDemoHashPassword(password, normalizedHash)) {
    return true;
  }

  return constantTimeEqual(password, normalizedHash);
}

function createAuthService(options = {}) {
  const authQuery = options.authQuery || createAuthQuery(options);
  const visitorQuery = options.visitorQuery || createVisitorQuery(options);
  const sessions = new Map();

  function createToken() {
    return crypto.randomBytes(24).toString('hex');
  }

  function createSession(user, meta = {}) {
    const token = createToken();
    const session = {
      token,
      user,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
      ...meta,
    };

    sessions.set(token, session);
    return session;
  }

  function issueVisitorSession(visitor, scope = 'REGISTERED') {
    const sessionUser = buildVisitorSessionVisitor(visitor, scope);
    const session = createSession(sessionUser, { accountType: 'VISITOR' });

    return {
      success: true,
      message: scope === 'TEMP' ? 'temporary visitor logged in' : 'visitor logged in',
      data: {
        token: session.token,
        user: session.user,
      },
    };
  }

  function issueAdminSession(admin) {
    const sessionUser = buildAdminSessionUser(admin);
    const session = createSession(sessionUser, { accountType: 'ADMIN' });

    return {
      success: true,
      message: 'admin logged in',
      data: {
        token: session.token,
        user: session.user,
      },
    };
  }

  function getTokenFromRequest(req) {
    const authorization = req.headers.authorization || req.headers.Authorization || '';
    if (authorization.startsWith('Bearer ')) {
      return authorization.slice(7).trim();
    }

    const tokenHeader = req.headers['x-auth-token'];
    if (isNonEmptyString(tokenHeader)) {
      return tokenHeader.trim();
    }

    return '';
  }

  function getSessionFromRequest(req) {
    const token = getTokenFromRequest(req);
    if (!token) {
      return null;
    }

    const session = sessions.get(token);
    if (!session) {
      return null;
    }

    if (session.expiresAt && new Date(session.expiresAt).getTime() <= Date.now()) {
      sessions.delete(token);
      return null;
    }

    return session;
  }

  function revokeToken(token) {
    if (sessions.has(token)) {
      sessions.delete(token);
    }
  }

  async function loginAdmin({ username, password } = {}) {
    if (!isNonEmptyString(username)) {
      throw new AppError(400, 'username is required');
    }

    if (!isNonEmptyString(password)) {
      throw new AppError(400, 'password is required');
    }

    if (typeof authQuery.findAdminByUsername !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const admin = await authQuery.findAdminByUsername(username.trim());
    if (!admin || admin.status !== 'ENABLED') {
      throw new AppError(401, 'invalid admin credentials');
    }

    if (!verifyAdminPassword(password, admin.passwordHash)) {
      throw new AppError(401, 'invalid admin credentials');
    }

    return issueAdminSession(admin);
  }

  async function loginVisitorTemp({ phone } = {}) {
    const normalizedPhone = normalizePhoneKey(phone);
    if (!isNonEmptyString(normalizedPhone)) {
      throw new AppError(400, 'phone is required');
    }

    if (typeof visitorQuery.findVisitorByPhone !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    let visitor = await visitorQuery.findVisitorByPhone(normalizedPhone);
    if (!visitor) {
      if (typeof visitorQuery.insertVisitor !== 'function') {
        throw new AppError(503, 'database is unavailable');
      }

      visitor = await visitorQuery.insertVisitor({
        visitorName: `临时游客${normalizedPhone.slice(-4)}`,
        idType: 'TEMP_PHONE',
        idNumber: normalizedPhone,
        phone: normalizedPhone,
        gender: null,
        birthDate: null,
      });
    }

    if (!visitor) {
      throw new AppError(500, 'failed to create visitor session');
    }

    const scope = visitor.idType === 'TEMP_PHONE' ? 'TEMP' : 'REGISTERED';
    return issueVisitorSession(visitor, scope);
  }

  async function loginRegisteredVisitor(visitor) {
    if (!visitor) {
      throw new AppError(500, 'failed to create visitor session');
    }

    return issueVisitorSession(visitor, 'REGISTERED');
  }

  async function getCurrentUser(req) {
    const session = getSessionFromRequest(req);
    if (!session) {
      throw new AppError(401, 'unauthorized');
    }

    return {
      success: true,
      message: 'session loaded',
      data: {
        token: session.token,
        user: session.user,
      },
    };
  }

  async function logout(req) {
    const token = getTokenFromRequest(req);
    if (token) {
      revokeToken(token);
    }

    return {
      success: true,
      message: 'logged out',
    };
  }

  function requireSession(allowedRoles = []) {
    return (req, _res, next) => {
      const session = getSessionFromRequest(req);

      if (!session) {
        next(new AppError(401, 'unauthorized'));
        return;
      }

      if (Array.isArray(allowedRoles) && allowedRoles.length > 0) {
        const roleOk = allowedRoles.includes(session.user.role);
        if (!roleOk) {
          next(new AppError(403, 'forbidden'));
          return;
        }
      }

      req.auth = session.user;
      req.authToken = session.token;
      next();
    };
  }

  function requireRegisteredVisitor() {
    return (req, _res, next) => {
      const session = getSessionFromRequest(req);
      if (!session) {
        next(new AppError(401, 'unauthorized'));
        return;
      }

      if (session.user.role !== 'VISITOR' || session.user.scope !== 'REGISTERED') {
        next(new AppError(403, 'registered visitor account required'));
        return;
      }

      req.auth = session.user;
      req.authToken = session.token;
      next();
    };
  }

  function requireAdmin() {
    return (req, _res, next) => {
      const session = getSessionFromRequest(req);
      if (!session) {
        next(new AppError(401, 'unauthorized'));
        return;
      }

      if (session.user.role !== 'ADMIN') {
        next(new AppError(403, 'forbidden'));
        return;
      }

      req.auth = session.user;
      req.authToken = session.token;
      next();
    };
  }

  function requireVisitorOrAdmin() {
    return (req, _res, next) => {
      const session = getSessionFromRequest(req);
      if (!session) {
        next(new AppError(401, 'unauthorized'));
        return;
      }

      if (session.user.role !== 'VISITOR' && session.user.role !== 'ADMIN') {
        next(new AppError(403, 'forbidden'));
        return;
      }

      req.auth = session.user;
      req.authToken = session.token;
      next();
    };
  }

  function getSessionUserFromRequest(req) {
    const session = getSessionFromRequest(req);
    return session ? session.user : null;
  }

  return {
    createSession,
    getCurrentUser,
    getSessionFromRequest,
    getSessionUserFromRequest,
    issueAdminSession,
    issueVisitorSession,
    loginAdmin,
    loginRegisteredVisitor,
    loginVisitorTemp,
    logout,
    requireAdmin,
    requireRegisteredVisitor,
    requireSession,
    requireVisitorOrAdmin,
    revokeToken,
  };
}

module.exports = {
  createAuthService,
  verifyAdminPassword,
};
