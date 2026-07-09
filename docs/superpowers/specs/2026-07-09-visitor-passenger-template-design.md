# 游客出行人模板与每票实名设计

## 背景

当前购票流程已经支持一个账号购买多张票，但订单明细只记录票种、时段、价格和票码，缺少“这一张票属于哪个实名游客”的信息。用户希望一个账号可以提前维护多位常用出行人，购票时直接选择；如果临时新填出行人，下单成功后自动保存为常用模板。

## 目标

- 一个账号可以维护多个常用出行人模板。
- 购票时买几张票，就必须给几张票分别选择或填写实名信息。
- 每张票保存独立的姓名、证件类型、证件号码和手机号。
- 同一实名人在同一票种、同一日期、同一时段只能购买一次。
- 新填写的实名信息在下单成功后自动保存为当前账号的模板。
- 模板支持列表、添加、编辑、删除。

## 不做的内容

- 不接复杂家庭成员账号体系，出行人只是当前账号下的实名模板。
- 不做证件照片上传、人脸识别或第三方实名核验。
- 不做跨账号共享模板。
- 不把出行人模板塞进 `visitor` 表，避免账号身份和实际出行人混在一起。

## 数据模型

新增 `visitor_passenger_template` 表：

```sql
id BIGSERIAL PRIMARY KEY
owner_visitor_id BIGINT NOT NULL REFERENCES visitor(id)
passenger_name VARCHAR(50) NOT NULL
id_type VARCHAR(20) NOT NULL
id_number VARCHAR(50) NOT NULL
phone VARCHAR(20) NOT NULL
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
UNIQUE (owner_visitor_id, id_type, id_number)
```

扩展 `ticket_order_item`：

```sql
passenger_template_id BIGINT REFERENCES visitor_passenger_template(id)
passenger_name VARCHAR(50) NOT NULL
passenger_id_type VARCHAR(20) NOT NULL
passenger_id_number VARCHAR(50) NOT NULL
passenger_phone VARCHAR(20) NOT NULL
```

新增业务唯一约束或唯一索引：

```sql
UNIQUE (ticket_type_id, time_slot_id, visit_date, passenger_id_type, passenger_id_number)
```

含义：同一个实名人在同一票种、同一日期、同一时段只能买一次。这个约束放在数据库层兜底，防止并发重复购票。

## 后端接口

新增出行人模板接口，全部要求游客登录：

```text
GET    /api/me/passenger-templates
POST   /api/me/passenger-templates
PATCH  /api/me/passenger-templates/{template_id}
DELETE /api/me/passenger-templates/{template_id}
```

权限规则：

- 只能查看、编辑、删除当前 session 对应游客自己的模板。
- 不接受前端传 `ownerVisitorId`。
- 新增和编辑时校验姓名、证件类型、证件号、手机号。
- 同一账号下同一证件号只能保留一份模板。

扩展创建订单接口：

```json
{
  "buyerName": "张三",
  "buyerPhone": "13900000000",
  "items": [
    {
      "productId": 1,
      "timeSlotId": 10,
      "visitDate": "2026-07-09",
      "passengers": [
        {
          "templateId": 3,
          "passengerName": "张三",
          "idType": "ID_CARD",
          "idNumber": "4503...",
          "phone": "13900000000"
        }
      ]
    }
  ]
}
```

调整点：

- `items[].quantity` 可以由 `passengers.length` 推导，也可以保留 `quantity` 并要求二者一致。推荐保留 `quantity`，校验 `quantity == passengers.length`，前端改动更小。
- 后端按乘客列表展开订单明细，一名乘客生成一条 `ticket_order_item`。
- 若 `templateId` 存在，必须属于当前登录游客；同时请求中的姓名、证件号、手机号必须与模板一致，避免前端借模板 ID 伪造数据。
- 若没有 `templateId`，下单成功后按证件号自动 upsert 到当前账号模板。
- 任何一张票缺少实名信息，返回 `422`。
- 同一订单内重复证件号，返回 `PASSENGER_DUPLICATED_IN_ORDER`。
- 已经买过同票种、同日期、同时段，返回 `PASSENGER_TIME_SLOT_DUPLICATED`。

## 前端流程

购票页新增“出行人信息”面板：

- 用户选票后，系统按总票数生成实名行。
- 每一行对应一张票，展示票种名称和序号，例如“成人票 1”“儿童票 1”。
- 每行可以从常用出行人模板中选择，也可以手动填写姓名、身份证号、手机号。
- 手动填写后不需要单独点“保存模板”，下单成功后自动保存。
- 如果减少购票数量，多出来的实名行自动移除。
- 提交按钮只有在每张票都有完整实名信息后才可用。

模板管理入口：

- 在“出行人信息”面板里提供“管理常用出行人”按钮。
- 用 Ant Design Modal 或 Drawer 展示模板列表。
- 支持新增、编辑、删除。
- 删除模板不影响已经生成的历史订单，因为订单明细已经保存了实名快照。

## 订单展示

游客订单详情和后台订单详情都显示每张票的实名信息：

- 游客端可以显示姓名、手机号脱敏、证件号脱敏。
- 后台详情也默认脱敏展示，除非后续明确需要完整证件号。
- 票码核销时仍以票码为主，但核销详情可以辅助显示乘客姓名。

## 安全与边界

- 出行人模板归属从 session 判断，不信任前端提交的用户 ID。
- 模板接口、订单创建接口都校验 CSRF。
- 证件号和手机号不进入公开列表的完整展示，页面和导出默认脱敏。
- 数据库唯一约束兜底同一实名人重复购票，避免并发绕过服务层校验。
- 删除模板只删除模板，不删除历史订单明细，保证审计可追溯。

## 测试计划

后端最小测试：

- 当前游客只能看到自己的模板。
- 新增、编辑、删除模板需要登录和 CSRF。
- 创建订单时每张票必须有乘客信息。
- `quantity` 与 `passengers.length` 不一致时拒绝。
- 同一订单内重复证件号时拒绝。
- 同一实名人在同一票种、同一日期、同一时段重复购票时拒绝。
- 新填写乘客下单成功后自动保存模板。
- 模板 ID 不属于当前游客时拒绝下单。

前端最小测试：

- 票数变化时实名行数量同步变化。
- 可以从模板选择出行人。
- 可以手动填写新出行人。
- 实名信息不完整时不能提交订单。
- 提交订单时请求体包含每张票的乘客信息。

## 答辩表述

本功能把“账号购票人”和“实际出行人”分开。账号负责登录和订单归属，出行人模板负责保存常用实名信息，每张票在订单明细中保存一份实名快照。这样既支持一个账号为多人购票，也能保证每张票都能追溯到具体游客；同时通过数据库唯一约束限制同一实名人在同一票种、同一日期、同一时段重复购票，避免实名制票务风险。
