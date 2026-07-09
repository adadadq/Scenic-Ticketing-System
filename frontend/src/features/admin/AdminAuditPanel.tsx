import {
  CalendarOutlined,
  CheckCircleOutlined,
  DownOutlined,
  DownloadOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  LoginOutlined,
  ReloadOutlined,
  SearchOutlined,
  SafetyCertificateOutlined,
  SunOutlined,
} from '@ant-design/icons'
import { Button, Input, Select, Typography } from 'antd'
import { useMemo, useState } from 'react'
import { AdminNoticeButton } from './components/AdminNoticeButton'
import './adminAudit.css'

const { Text, Title } = Typography

type AuditLog = {
  actor: string
  actorAccount: string
  browser: string
  changeSummary: string
  id: string
  ip: string
  object: string
  requestId: string
  result: '成功' | '警告'
  source: string
  steps: string[]
  time: string
  title: string
  type: '登录后台' | '修改票价' | '核验入园' | '发起退款' | '导出报表' | '修改管理员账号'
  tone: 'teal' | 'orange' | 'green' | 'blue'
}

const auditLogs: AuditLog[] = [
  {
    actor: '演示管理员',
    actorAccount: '@admin',
    browser: 'Chrome / Windows',
    changeSummary: '本次操作无数据变更',
    id: 'LOG20260628160215A1B2C',
    ip: '192.168.1.10',
    object: '运营后台',
    requestId: 'req-81d6b6d3775440fd9719f7c736340fb7',
    result: '成功',
    source: 'Chrome / Windows 11',
    steps: ['提交登录请求', '验证账号密码', '校验权限通过', '登录成功'],
    time: '2026-06-28 16:02:15',
    title: '登录后台',
    type: '登录后台',
    tone: 'teal',
  },
  {
    actor: '演示管理员',
    actorAccount: '@admin',
    browser: 'Chrome / Windows',
    changeSummary: '遇龙河成人票价格由 118 调整为 128',
    id: 'LOG20260628154532B2C3D',
    ip: '192.168.1.10',
    object: '遇龙河成人票',
    requestId: 'req-price-260628-154532',
    result: '成功',
    source: 'Chrome / Windows',
    steps: ['打开票种管理', '提交价格调整', '写入审计记录', '保存成功'],
    time: '2026-06-28 15:45:32',
    title: '修改票价',
    type: '修改票价',
    tone: 'orange',
  },
  {
    actor: '李四',
    actorAccount: '@lisi',
    browser: 'Android / Mobile',
    changeSummary: '票码核验成功，订单状态同步更新',
    id: 'LOG20260628152008C3D4E',
    ip: '192.168.1.25',
    object: '遇龙河成人票',
    requestId: 'req-checkin-260628-152008',
    result: '成功',
    source: 'Android / Mobile',
    steps: ['扫描票码', '校验订单状态', '写入核验记录', '允许入园'],
    time: '2026-06-28 15:20:08',
    title: '核验入园',
    type: '核验入园',
    tone: 'green',
  },
  {
    actor: '王五',
    actorAccount: '@wangwu',
    browser: 'iOS / Mobile',
    changeSummary: '儿童票退款进入处理队列',
    id: 'LOG20260628145047D4E5F',
    ip: '192.168.1.30',
    object: '遇龙河儿童票',
    requestId: 'req-refund-260628-145047',
    result: '成功',
    source: 'iOS / Mobile',
    steps: ['读取订单', '校验退款条件', '提交退款申请', '等待处理'],
    time: '2026-06-28 14:50:47',
    title: '发起退款',
    type: '发起退款',
    tone: 'orange',
  },
  {
    actor: '张三',
    actorAccount: '@zhangsan',
    browser: 'Chrome / Windows',
    changeSummary: '销售报表导出任务已创建',
    id: 'LOG20260628141022E5F6G',
    ip: '192.168.1.10',
    object: '销售报表',
    requestId: 'req-export-260628-141022',
    result: '成功',
    source: 'Chrome / Windows',
    steps: ['选择日期范围', '创建导出任务', '生成下载文件', '任务完成'],
    time: '2026-06-28 14:10:22',
    title: '导出报表',
    type: '导出报表',
    tone: 'blue',
  },
  {
    actor: '演示管理员',
    actorAccount: '@admin',
    browser: 'Chrome / Windows',
    changeSummary: '管理员账号资料发生变更，请复核',
    id: 'LOG20260628133056F6G7H',
    ip: '192.168.1.10',
    object: '演示管理员',
    requestId: 'req-profile-260628-133056',
    result: '警告',
    source: 'Chrome / Windows',
    steps: ['打开账号设置', '提交资料修改', '触发风险提示', '记录审计日志'],
    time: '2026-06-28 13:30:56',
    title: '修改管理员账号',
    type: '修改管理员账号',
    tone: 'orange',
  },
]

const typeOptions = [
  { label: '操作类型', value: 'ALL' },
  ...Array.from(new Set(auditLogs.map((item) => item.type))).map((value) => ({ label: value, value })),
]

const actorOptions = [
  { label: '操作人', value: 'ALL' },
  ...Array.from(new Set(auditLogs.map((item) => item.actor))).map((value) => ({ label: value, value })),
]

const metrics = [
  { icon: <SafetyCertificateOutlined />, label: '今日操作', tone: 'teal', trend: '+18.75% ↑', value: '128' },
  { icon: <ExclamationCircleOutlined />, label: '高风险操作', tone: 'orange', trend: '-25.00% ↓', value: '3' },
  { icon: <CheckCircleOutlined />, label: '核验记录', tone: 'green', trend: '+12.50% ↗', value: '86' },
  { icon: <DownloadOutlined />, label: '导出任务', tone: 'blue', trend: '+9.09% ↗', value: '12' },
]

type AdminAuditPanelProps = {
  onOpenProfile?: () => void
}

export function AdminAuditPanel({ onOpenProfile }: AdminAuditPanelProps) {
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState('ALL')
  const [actor, setActor] = useState('ALL')
  const [selectedId, setSelectedId] = useState(auditLogs[0]?.id)
  const logs = useMemo(() => auditLogs.filter((log) => {
    const matchesType = type === 'ALL' || log.type === type
    const matchesActor = actor === 'ALL' || log.actor === actor
    const q = keyword.trim().toLowerCase()
    const matchesKeyword = !q || [log.id, log.actor, log.object, log.type, log.ip].some((value) => value.toLowerCase().includes(q))

    return matchesType && matchesActor && matchesKeyword
  }), [actor, keyword, type])
  const selectedLog = logs.find((log) => log.id === selectedId) ?? logs[0]

  function exportVisibleLogs() {
    const header = ['时间', '操作人', '操作类型', '对象', '结果', '请求来源']
    const rows = logs.map((log) => [log.time, log.actor, log.type, log.object, log.result, log.source])
    const csv = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n')
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'admin-audit-logs.csv'
    document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  }

  return (
    <section className="admin-audit-page">
      <header className="admin-audit-hero">
        <div className="admin-audit-hero-copy">
          <Title level={1}>审计日志</Title>
          <Text>操作留痕、核验记录与安全追踪</Text>
          <span aria-hidden="true" />
        </div>
        <div className="admin-dashboard-top-actions">
          <div className="admin-weather-card">
            <SunOutlined />
            <span>晴 26°C</span>
            <Text>2026-06-28 16:04</Text>
          </div>
          <AdminNoticeButton />
          <button className="admin-profile-button" type="button" onClick={onOpenProfile}>
            <span className="admin-profile-avatar" />
            <strong>演示管理员</strong>
            <DownOutlined />
          </button>
        </div>
      </header>

      <div className="admin-audit-body">
        <div className="admin-audit-toolbar">
          <div className="admin-audit-date" aria-label="统计周期">
            <CalendarOutlined />
            <span>2026/06/26&nbsp;&nbsp;~&nbsp;&nbsp;2026/06/28</span>
          </div>
          <Select className="admin-audit-select" options={typeOptions} value={type} onChange={setType} />
          <Select className="admin-audit-select" options={actorOptions} value={actor} onChange={setActor} />
          <Input
            allowClear
            className="admin-audit-search"
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="关键词搜索"
            prefix={<SearchOutlined />}
            value={keyword}
          />
          <div className="admin-audit-toolbar-spacer" />
          <Button icon={<ReloadOutlined />} onClick={() => {
            setKeyword('')
            setType('ALL')
            setActor('ALL')
          }}>
            刷新
          </Button>
          <Button className="admin-audit-export" icon={<DownloadOutlined />} onClick={exportVisibleLogs}>
            导出日志
          </Button>
        </div>

        <div className="admin-audit-layout">
          <section className="admin-audit-list-card">
            <div className="admin-audit-card-title">日志列表</div>
            <div className="admin-audit-table-wrap">
              <table className="admin-audit-table">
                <thead>
                  <tr>
                    <th />
                    <th>时间</th>
                    <th>操作人</th>
                    <th>操作类型</th>
                    <th>对象</th>
                    <th>结果</th>
                    <th>请求来源</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr className={selectedLog?.id === log.id ? 'is-selected' : undefined} key={log.id} onClick={() => setSelectedId(log.id)}>
                      <td><span className={`admin-audit-row-icon is-${log.tone}`}>{auditIcon(log.type)}</span></td>
                      <td><strong>{log.time}</strong></td>
                      <td>
                        <div className="admin-audit-actor">
                          <strong>{log.actor}</strong>
                          <Text>{log.actorAccount}</Text>
                        </div>
                      </td>
                      <td><span className={`admin-audit-type is-${log.tone}`}>{log.type}</span></td>
                      <td>{log.object}</td>
                      <td><span className={`admin-audit-result is-${log.result === '成功' ? 'success' : 'warn'}`}>{log.result}</span></td>
                      <td>
                        <div className="admin-audit-source">
                          <strong>{log.ip}</strong>
                          <Text>{log.browser}</Text>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!logs.length ? (
                    <tr className="admin-audit-empty-row">
                      <td className="admin-audit-empty-cell" colSpan={7}>暂无匹配的审计日志</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
            <div className="admin-audit-pagination">
              <Text>共 {logs.length} 条</Text>
              <span>10条/页</span>
              <span aria-label="上一页">‹</span>
              <span className="is-active">1</span>
              <span aria-label="下一页">›</span>
            </div>
          </section>

          <AuditDetailCard log={selectedLog} />
        </div>

        <div className="admin-audit-metrics">
          {metrics.map((metric) => (
            <section className={`admin-audit-metric is-${metric.tone}`} key={metric.label}>
              <span>{metric.icon}</span>
              <div>
                <Text>{metric.label}</Text>
                <strong>{metric.value}<em>次</em></strong>
                <small>较昨日 {metric.trend}</small>
              </div>
            </section>
          ))}
        </div>
      </div>
    </section>
  )
}

function AuditDetailCard({ log }: { log?: AuditLog }) {
  if (!log) {
    return (
      <aside className="admin-audit-detail-card">
        <div className="admin-audit-card-title">日志详情</div>
        <div className="admin-audit-empty-detail">
          <SearchOutlined />
          <strong>暂无日志详情</strong>
          <Text>请调整操作类型、操作人或关键词后再查看。</Text>
        </div>
      </aside>
    )
  }

  return (
    <aside className="admin-audit-detail-card">
      <div className="admin-audit-card-title">日志详情</div>
      <div className="admin-audit-detail-head">
        <span className={`admin-audit-row-icon is-${log.tone}`}>{auditIcon(log.type)}</span>
        <div>
          <strong>{log.title}</strong>
          <Text>{log.time}</Text>
        </div>
        <span className={`admin-audit-result is-${log.result === '成功' ? 'success' : 'warn'}`}>{log.result}</span>
      </div>

      <div className="admin-audit-detail-lines">
        <DetailLine label="操作编号" value={log.id} />
        <DetailLine label="操作人" value={`${log.actor}（${log.actorAccount}）`} />
        <DetailLine label="角色" value="超级管理员" />
        <DetailLine label="IP 地址" value={log.ip} />
        <DetailLine label="请求编号" value={log.requestId} />
        <DetailLine label="请求来源" value={log.source} />
      </div>

      <div className="admin-audit-timeline">
        <strong>操作时间线</strong>
        {log.steps.map((step) => (
          <div className="admin-audit-timeline-row" key={step}>
            <span />
            <Text>{log.time.slice(11)}</Text>
            <em>{step}</em>
          </div>
        ))}
      </div>

      <div className="admin-audit-change-card">
        <strong>变更前后摘要</strong>
        <Text>{log.changeSummary}</Text>
      </div>
    </aside>
  )
}

function DetailLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="admin-audit-detail-line">
      <Text>{label}</Text>
      <strong>{value}</strong>
    </div>
  )
}

function auditIcon(type: AuditLog['type']) {
  if (type === '登录后台') {
    return <SafetyCertificateOutlined />
  }

  if (type === '修改票价' || type === '修改管理员账号') {
    return <EditOutlined />
  }

  if (type === '导出报表') {
    return <DownloadOutlined />
  }

  if (type === '发起退款') {
    return '¥'
  }

  return <LoginOutlined />
}
