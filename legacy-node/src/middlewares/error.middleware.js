const { sendJson } = require('../utils/response');

function translateDatabaseError(err) {
  if (!err || typeof err !== 'object') {
    return null;
  }

  const constraint = String(err.constraint || err.message || '');
  if (err.code === '23505') {
    if (constraint.includes('uk_visitor_id_doc')) {
      return '该证件号码已经注册，请更换证件号码或使用原账号登录。';
    }
    if (constraint.includes('uk_visitor_phone')) {
      return '该手机号已经注册，请直接用手机号登录或更换手机号。';
    }
    if (constraint.includes('uk_ticket_type_spot_name')) {
      return '该景区下已存在同名票种（已停用票种也会占用名称）。';
    }
    if (constraint.includes('uq_route_product_ticket_type')) {
      return '该票种已经绑定线路产品，请先停用原线路再新增。';
    }
    if (constraint.includes('uq_pier_scenic_name')) {
      return '该景区下已存在同名码头。';
    }
    if (constraint.includes('uq_offline_sale_notice_product_date')) {
      return '当天已存在该线路的窗口状态。';
    }
    return '提交的数据已存在，请检查是否重复。';
  }

  if (err.code === '23503') {
    return '关联数据不存在，请检查后重试。';
  }

  if (err.code === '23502') {
    return '必填信息不能为空，请补充后重试。';
  }

  if (err.code === '23514') {
    if (constraint.includes('ck_route_product_distinct_pier')) {
      return '起点码头和终点码头不能相同。';
    }
    if (constraint.includes('ck_route_product_sale_price')) {
      return '售价必须大于或等于 0。';
    }
    if (constraint.includes('ck_route_product_raft_capacity')) {
      return '每筏人数必须大于 0。';
    }
    return '提交内容不符合业务规则，请检查后重试。';
  }

  if (err.code === '22P02') {
    return '提交内容格式不正确，请检查后重试。';
  }

  return null;
}

function errorMiddleware(err, _req, res, _next) {
  const isObject = err !== null && typeof err === 'object';
  const statusCode = isObject && Number.isInteger(err.statusCode) ? err.statusCode : 500;
  const databaseMessage = translateDatabaseError(err);
  const message = databaseMessage
    || (isObject && typeof err.message === 'string' && err.message ? err.message : 'Internal Server Error');

  sendJson(res, statusCode, {
    success: false,
    message,
  });
}

module.exports = {
  errorMiddleware,
};
