const express = require('express');

const { createManageController } = require('../controllers/manage.controller');

function createManageRouter(options = {}) {
  const manageController = options.manageController
    || createManageController({ manageService: options.manageService });

  const router = express.Router();

  router.get('/visitors', manageController.getVisitors);
  router.post('/visitors', manageController.postVisitor);
  router.get('/visitors/:visitorId/orders', manageController.getVisitorOrders);
  router.get('/visitors/:visitorId', manageController.getVisitorById);
  router.get('/routes', manageController.getRoutes);
  router.get('/status/lines', manageController.getRoutes);
  router.get('/status/docks', manageController.getPiers);
  router.get('/status/windows', manageController.getOfflineSaleNotices);
  router.get('/orders/by-phone', manageController.getOrdersByPhone);
  router.get('/admin/inventory', manageController.getInventory);

  router.get('/admin/piers', manageController.getPiers);
  router.get('/admin/wharves', manageController.getPiers);
  router.get('/admin/docks', manageController.getPiers);
  router.post('/admin/piers', manageController.postPier);
  router.post('/admin/wharves', manageController.postPier);
  router.post('/admin/docks', manageController.postPier);
  router.put('/admin/piers/:id', manageController.putPier);
  router.put('/admin/wharves/:id', manageController.putPier);
  router.put('/admin/docks/:id', manageController.putPier);
  router.delete('/admin/piers/:id', manageController.deletePier);
  router.delete('/admin/wharves/:id', manageController.deletePier);
  router.delete('/admin/docks/:id', manageController.deletePier);

  router.get('/admin/route-products', manageController.getRouteProducts);
  router.get('/admin/ticket-types', manageController.getRouteProducts);
  router.get('/admin/line-products', manageController.getRouteProducts);
  router.post('/admin/route-products', manageController.postRouteProduct);
  router.post('/admin/ticket-types', manageController.postRouteProduct);
  router.post('/admin/line-products', manageController.postRouteProduct);
  router.put('/admin/route-products/:id', manageController.putRouteProduct);
  router.patch('/admin/ticket-types/:id', manageController.putRouteProduct);
  router.put('/admin/line-products/:id', manageController.putRouteProduct);
  router.delete('/admin/route-products/:id', manageController.deleteRouteProduct);
  router.delete('/admin/ticket-types/:id', manageController.deleteRouteProduct);
  router.delete('/admin/line-products/:id', manageController.deleteRouteProduct);

  router.get('/admin/offline-sale-notices', manageController.getOfflineSaleNotices);
  router.get('/admin/sales-windows', manageController.getOfflineSaleNotices);
  router.get('/admin/windows', manageController.getOfflineSaleNotices);
  router.post('/admin/offline-sale-notices', manageController.postOfflineSaleNotice);
  router.post('/admin/sales-windows', manageController.postOfflineSaleNotice);
  router.post('/admin/windows', manageController.postOfflineSaleNotice);
  router.patch('/admin/offline-sale-notices/:id', manageController.putOfflineSaleNotice);
  router.patch('/admin/sales-windows/:id', manageController.putOfflineSaleNotice);
  router.patch('/admin/windows/:id', manageController.putOfflineSaleNotice);
  router.put('/admin/offline-sale-notices/:id', manageController.putOfflineSaleNotice);
  router.put('/admin/sales-windows/:id', manageController.putOfflineSaleNotice);
  router.put('/admin/windows/:id', manageController.putOfflineSaleNotice);
  router.delete('/admin/offline-sale-notices/:id', manageController.deleteOfflineSaleNotice);
  router.delete('/admin/sales-windows/:id', manageController.deleteOfflineSaleNotice);
  router.delete('/admin/windows/:id', manageController.deleteOfflineSaleNotice);

  router.get('/admin/operation-logs', manageController.getOperationLogs);

  return router;
}

module.exports = {
  createManageRouter,
};
