import {
  CalendarOutlined,
  ClockCircleOutlined,
  CompassOutlined,
  CustomerServiceOutlined,
  EnvironmentOutlined,
  FileProtectOutlined,
  OrderedListOutlined,
  PhoneOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  SoundOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Button, Card, Col, Flex, Row, Typography } from 'antd'
import { useCurrentAnnouncementQuery } from '../announcements/queries'

const { Text, Title } = Typography

type VisitorServiceWorkbenchProps = {
  onOpenBooking?: () => void
  onOpenOrders?: () => void
}

const summaryItems = [
  { icon: <CalendarOutlined />, label: '今日开放', note: '景区正常开放', value: '放心出行' },
  { icon: <ClockCircleOutlined />, label: '售票时间', note: '竹筏漂流售票时段', value: '08:30-16:30' },
  { icon: <UserOutlined />, label: '入园时间', note: '景区入园时段', value: '09:00-17:30' },
  { icon: <CustomerServiceOutlined />, label: '客服时间', note: '如需帮助请联系客服', value: '08:30-18:00' },
]

const routeStops = [
  { title: '阳朔县城', subtitle: '出发地', glyph: '亭' },
  { title: '金龙桥码头', subtitle: '检票候筏', glyph: '桥' },
  { title: '遇龙河竹筏', subtitle: '漂流游览', glyph: '竹' },
  { title: '旧县码头', subtitle: '到达点', glyph: '门' },
]

const guideCards = [
  {
    icon: <EnvironmentOutlined />,
    title: '到达建议',
    items: ['建议提前 30 分钟到达码头', '节假日和周末客流较大', '停车推荐官方停车场', '返程可在旧县码头附近换乘'],
  },
  {
    icon: <SafetyCertificateOutlined />,
    title: '入园准备',
    items: ['携带本人身份证件', '儿童、老人需购票', '穿着防滑鞋，做好防晒', '如遇降雨，注意安全'],
  },
  {
    icon: <CompassOutlined />,
    title: '路线建议',
    items: ['自驾：导航至金龙桥码头', '县城出发优先选景区接驳车', '返程可在旧县码头附近换乘'],
  },
  {
    icon: <FileProtectOutlined />,
    title: '退改规则',
    items: ['未核验订单可在游玩日前取消', '已核验票码不能退款', '多人订单按未使用票项处理'],
  },
  {
    icon: <QuestionCircleOutlined />,
    title: '常见问题',
    items: ['支付后在哪里查看门票？', '儿童需要购票吗？', '竹筏漂流安全吗？', '发票如何申请？'],
  },
]

const bottomItems = [
  { icon: <PhoneOutlined />, title: '联系景区', text: '咨询时间 08:30-18:00' },
  { icon: <SafetyCertificateOutlined />, title: '官方服务', text: '官方票务 · 安全可靠' },
  { icon: <UserOutlined />, title: '现场服务台', text: '码头现场优先受理' },
  { icon: <SoundOutlined />, title: '温馨提示', text: '水上活动，注意安全，听从工作人员指引' },
]

function RouteMap() {
  return (
    <svg aria-hidden="true" className="visitor-service-map" viewBox="0 0 640 180">
      <defs>
        <linearGradient id="serviceRiver" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stopColor="#44c3c4" />
          <stop offset="1" stopColor="#0b8b86" />
        </linearGradient>
      </defs>
      <path d="M0 138 C96 106 128 152 214 122 C302 90 346 138 430 100 C510 64 562 82 640 48 L640 180 L0 180 Z" fill="#dff3df" />
      <path d="M0 130 C88 94 132 140 218 112 C308 82 344 132 428 94 C506 58 556 76 640 42" fill="none" stroke="#f8fff7" strokeDasharray="18 12" strokeWidth="30" />
      <path d="M0 130 C88 94 132 140 218 112 C308 82 344 132 428 94 C506 58 556 76 640 42" fill="none" stroke="url(#serviceRiver)" strokeLinecap="round" strokeWidth="22" />
      <path d="M0 130 C88 94 132 140 218 112 C308 82 344 132 428 94 C506 58 556 76 640 42" fill="none" stroke="#f7f5bd" strokeDasharray="6 12" strokeLinecap="round" strokeWidth="4" />
      <path d="M36 146 C110 118 172 124 242 140 C300 154 370 148 452 122 C514 102 570 92 625 98" fill="none" stroke="#8fbc91" strokeDasharray="8 8" strokeWidth="5" />
      <g fill="#b7dba8" opacity="0.95">
        <path d="M56 70 l34 -30 l34 30 Z" />
        <path d="M126 84 l38 -38 l38 38 Z" />
        <path d="M244 74 l42 -42 l42 42 Z" />
        <path d="M510 70 l36 -34 l36 34 Z" />
      </g>
      <g fill="#0b776f">
        <circle cx="78" cy="118" r="10" />
        <path d="M78 128 l-8 20 h16 Z" />
        <path d="M350 96 l20 14 h-40 Z" />
        <path d="M350 74 v44" stroke="#0b776f" strokeLinecap="round" strokeWidth="7" />
      </g>
      <g fill="#f28d39">
        <circle cx="594" cy="66" r="13" />
        <circle cx="594" cy="66" r="5" fill="#fff" />
      </g>
    </svg>
  )
}

export function VisitorServiceWorkbench({ onOpenOrders }: VisitorServiceWorkbenchProps) {
  const announcementQuery = useCurrentAnnouncementQuery()
  const announcement = announcementQuery.data

  return (
    <section className="visitor-service-page">
      <section className="visitor-service-hero" aria-label="游客服务">
        <div className="visitor-service-hero-copy">
          <Title level={1}>游客服务</Title>
          <Text>开放时间、路线、入园准备和退改说明</Text>
          <span className="visitor-service-hero-mark" />
        </div>
        <Button className="visitor-service-order-btn" icon={<OrderedListOutlined />} onClick={onOpenOrders}>
          我的订单
        </Button>
      </section>

      {announcement ? (
        <section className="visitor-service-announcement">
          <SoundOutlined />
          <div>
            <strong>{announcement.title}</strong>
            <Text>{announcement.content}</Text>
          </div>
        </section>
      ) : null}

      <section className="visitor-service-summary" aria-label="今日服务状态">
        {summaryItems.map((item) => (
          <div className="visitor-service-summary-item" key={item.label}>
            <span className="visitor-service-summary-icon">{item.icon}</span>
            <div>
              <Text className="visitor-service-summary-label">{item.label}</Text>
              <strong>{item.value}</strong>
              <Text className="visitor-service-summary-note">{item.note}</Text>
            </div>
          </div>
        ))}
      </section>

      <Row className="visitor-service-layout" gutter={[18, 18]}>
        <Col xs={24} xl={11}>
          <Card className="workspace-card visitor-service-route-card" title="推荐路线">
            <div className="visitor-service-route">
              {routeStops.map((stop, index) => (
                <div className="visitor-service-stop" key={stop.title}>
                  <span className="visitor-service-step-index">{index + 1}</span>
                  <span className="visitor-service-stop-art">{stop.glyph}</span>
                  <Text className="visitor-service-stop-title">{stop.title}</Text>
                  <Text className="visitor-service-stop-subtitle">{stop.subtitle}</Text>
                </div>
              ))}
            </div>
            <RouteMap />
          </Card>
        </Col>

        <Col xs={24} xl={13}>
          <Row className="visitor-service-grid" gutter={[18, 18]}>
            {guideCards.map((card, index) => (
              <Col key={card.title} xs={24} md={index < 2 ? 12 : 8}>
                <Card className="workspace-card visitor-service-card">
                  <Flex align="center" gap={12}>
                    <span className="visitor-service-icon" aria-hidden="true">{card.icon}</span>
                    <Title level={2}>{card.title}</Title>
                  </Flex>
                  <ul>
                    {card.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Card>
              </Col>
            ))}
          </Row>
        </Col>
      </Row>

      <section className="visitor-service-bottom" aria-label="游客服务保障">
        {bottomItems.map((item) => (
          <div className="visitor-service-bottom-item" key={item.title}>
            <span>{item.icon}</span>
            <div>
              <strong>{item.title}</strong>
              <small>{item.text}</small>
            </div>
          </div>
        ))}
      </section>
    </section>
  )
}
