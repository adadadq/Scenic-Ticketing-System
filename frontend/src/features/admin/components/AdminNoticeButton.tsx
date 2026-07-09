import { BellOutlined } from '@ant-design/icons'
import { Popover, Typography } from 'antd'
import { useCurrentAnnouncementQuery } from '../../announcements/queries'

const { Text } = Typography

const systemNotices = [
  ['客流提醒', '10:30-12:30 为高峰时段，请提前安排核验。'],
  ['退款待处理', '3 笔订单申请退款，待后台处理。'],
  ['库存提醒', '遇龙河成人票库存偏低，请及时补充。'],
]

export function AdminNoticeButton() {
  const announcementQuery = useCurrentAnnouncementQuery()
  const announcement = announcementQuery.data
  const count = systemNotices.length + (announcement ? 1 : 0)

  return (
    <Popover
      arrow={false}
      content={(
        <div className="admin-notice-popover">
          <strong>通知</strong>
          {announcement ? (
            <div className="admin-notice-popover-item is-primary">
              <Text>{announcement.title}</Text>
              <span>{announcement.content}</span>
            </div>
          ) : null}
          {systemNotices.map(([title, content]) => (
            <div className="admin-notice-popover-item" key={title}>
              <Text>{title}</Text>
              <span>{content}</span>
            </div>
          ))}
        </div>
      )}
      placement="bottomRight"
      trigger="click"
    >
      <button className="admin-notice-button" type="button" aria-label="通知">
        <BellOutlined />
        <span>{count}</span>
      </button>
    </Popover>
  )
}
