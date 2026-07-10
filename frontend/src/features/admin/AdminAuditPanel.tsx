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
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Input, Select, Typography } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { adminAuditLogsApi } from '../../shared/api/endpoints'
import { formatApiError } from '../../shared/api/errors'
import type { AdminAuditLog, AdminAuditLogType } from '../../shared/api/types'
import { AdminNoticeButton } from './components/AdminNoticeButton'
import './adminAudit.css'

const { Text, Title } = Typography

type AuditTone = 'teal' | 'orange' | 'green' | 'blue'
type AuditViewLog = AdminAuditLog & {
  actor: string
  actorAccount: string
  changeSummary: string
  ip: string
  source: string
  steps: string[]
  time: string
  title: string
  tone: AuditTone
}

const typeTone: Record<AdminAuditLogType, AuditTone> = {
  发起退款: 'orange',
  核验入园: 'green',
  核验失败: 'orange',
  系统设置: 'blue',
  票种管理: 'teal',
}

type AdminAuditPanelProps = {
  onOpenProfile?: () => void
}

export function AdminAuditPanel({ onOpenProfile }: AdminAuditPanelProps) {
  const [keyword, setKeyword] = useState('')
  const [type, setType] = useState<AdminAuditLogType | 'ALL'>('ALL')
  const [actor, setActor] = useState('ALL')
  const [selectedId, setSelectedId] = useState<string>()
  const auditLogsQuery = useQuery({ queryKey: ['admin-audit-logs'], queryFn: () => adminAuditLogsApi.list() })
  const allLogs = useMemo(() => (auditLogsQuery.data?.items ?? []).map(toViewLog), [auditLogsQuery.data])
  const typeOptions = useMemo(() => [
    { label: '操作类型', value: 'ALL' },
    ...Array.from(new Set(allLogs.map((item) => item.type))).map((value) => ({ label: value, value })),
  ], [allLogs])
  const actorOptions = useMemo(() => [
    { label: '操作人', value: 'ALL' },
    ...Array.from(new Set(allLogs.map((item) => item.actor))).map((value) => ({ label: value, value })),
  ], [allLogs])
  const logs = useMemo(() => allLogs.filter((log) => {
    const matchesType = type === 'ALL' || log.type === type
    const matchesActor = actor === 'ALL' || log.actor === actor
    const q = keyword.trim().toLowerCase()
    const matchesKeyword = !q || [log.id, log.actor, log.object, log.type, log.ip, log.deviceId ?? ''].some((value) => value.toLowerCase().includes(q))

    return matchesType && matchesActor && matchesKeyword
  }), [actor, allLogs, keyword, type])
  const selectedLog = logs.find((log) => log.id === selectedId) ?? logs[0]
  const metrics = useMemo(() => buildMetrics(allLogs), [allLogs])

  useEffect(() => {
    if (!selectedLog && logs[0]) setSelectedId(logs[0].id)
  }, [logs, selectedLog])

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
        {auditLogsQuery.isError ? (
          <Alert showIcon type="error" message={formatApiError(auditLogsQuery.error, '审计日志加载失败，请稍后重试。')} />
        ) : null}
        <div className="admin-audit-toolbar">
          <div className="admin-audit-date" aria-label="统计周期">
            <CalendarOutlined />
            <span>最近 {auditLogsQuery.data?.total ?? 0} 条真实记录</span>
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
          <Button icon={<ReloadOutlined />} loading={auditLogsQuery.isFetching} onClick={() => {
            setKeyword('')
            setType('ALL')
            setActor('ALL')
            auditLogsQuery.refetch()
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
                          <Text>{log.source}</Text>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!logs.length ? (
                    <tr className="admin-audit-empty-row">
                      <td className="admin-audit-empty-cell" colSpan={7}>
                        {auditLogsQuery.isLoading ? '正在加载审计日志' : '暂无匹配的审计日志'}
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
            <div className="admin-audit-pagination">
              <Text>共 {logs.length} 条</Text>
              <span>20条/页</span>
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
                <small>{metric.caption}</small>
              </div>
            </section>
          ))}
        </div>
      </div>
    </section>
  )
}

function toViewLog(log: AdminAuditLog): AuditViewLog {
  const time = new Date(log.createdAt).toLocaleString('zh-CN', { hour12: false })
  return {
    ...log,
    actor: log.operatorDisplayName,
    actorAccount: `@${log.operatorUsername}`,
    changeSummary: log.action,
    ip: log.sourceIp ?? '未记录',
    source: log.deviceId ? `设备 ${log.deviceId}` : '历史记录未采集设备',
    steps: ['读取真实审计记录', log.action, '返回审计列表'],
    time,
    title: log.type,
    tone: typeTone[log.type],
  }
}

function buildMetrics(logs: AuditViewLog[]) {
  return [
    { icon: <SafetyCertificateOutlined />, label: '全部操作', tone: 'teal' as const, caption: '真实记录合计', value: String(logs.length) },
    { icon: <ExclamationCircleOutlined />, label: '风险提示', tone: 'orange' as const, caption: '失败或警告记录', value: String(logs.filter((log) => log.result === '警告').length) },
    { icon: <CheckCircleOutlined />, label: '核验记录', tone: 'green' as const, caption: '入园核验相关', value: String(logs.filter((log) => log.type.includes('核验')).length) },
    { icon: <DownloadOutlined />, label: '退款记录', tone: 'blue' as const, caption: '退款审计相关', value: String(logs.filter((log) => log.type === '发起退款').length) },
  ]
}

function AuditDetailCard({ log }: { log?: AuditViewLog }) {
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
        <DetailLine label="IP 地址" value={log.ip} />
        <DetailLine label="设备编号" value={log.deviceId ?? '历史记录未采集'} />
        <DetailLine label="登录会话" value={log.adminSessionId ? String(log.adminSessionId) : '历史记录未采集'} />
        <DetailLine label="浏览器环境" value={log.userAgent ?? '历史记录未采集'} />
        <DetailLine label="请求编号" value={log.requestId ?? '未记录'} />
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
        <strong>变更摘要</strong>
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

function auditIcon(type: AdminAuditLogType) {
  if (type === '系统设置' || type === '票种管理') {
    return <EditOutlined />
  }

  if (type === '发起退款') {
    return '¥'
  }

  return <LoginOutlined />
}
