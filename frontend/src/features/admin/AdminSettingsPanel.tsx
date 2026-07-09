import {
  BellOutlined,
  CalendarOutlined,
  CloudDownloadOutlined,
  DatabaseOutlined,
  DownOutlined,
  ExportOutlined,
  SafetyCertificateOutlined,
  SunOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { Alert, Button, Input, InputNumber, Switch, Typography } from 'antd'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { adminSettingsApi } from '../../shared/api/endpoints'
import type { AdminSystemSettings, AdminSystemSettingsUpdateRequest } from '../../shared/api/types'
import { AdminNoticeButton } from './components/AdminNoticeButton'
import './adminSettings.css'

const { Text, Title } = Typography

type AdminSettingsPanelProps = {
  onOpenProfile?: () => void
}

const defaultSettings: AdminSystemSettings = {
  scenicName: '遇龙河景区',
  serviceTimeStart: '08:30',
  serviceTimeEnd: '18:00',
  ticketTimeStart: '08:30',
  ticketTimeEnd: '16:30',
  checkInTimeStart: '09:00',
  checkInTimeEnd: '17:30',
  perOrderLimit: 10,
  sessionTtlMinutes: 30,
  csrfEnabled: true,
  loginGuardEnabled: true,
  smsEnabled: true,
  mailEnabled: true,
  refundEnabled: true,
  stockEnabled: true,
  auditRetentionDays: 90,
  lastBackupLabel: '今天 02:30',
  recentLogs: [],
}

function buildOverviewCards(settings: AdminSystemSettings) {
  return [
    { icon: <SafetyCertificateOutlined />, title: '账号安全', lines: ['密码强度：强', `会话有效期：${settings.sessionTtlMinutes} 分钟`], tone: 'teal' },
    { icon: <BellOutlined />, title: '通知服务', lines: [settings.smsEnabled || settings.mailEnabled ? '短信/邮件正常' : '通知已关闭', settings.stockEnabled ? '库存预警：已启用' : '库存预警：已关闭'], tone: 'orange' },
    { icon: <DatabaseOutlined />, title: '数据维护', lines: [`最后备份：${settings.lastBackupLabel}`, `审计保留：${settings.auditRetentionDays} 天`], tone: 'blue' },
    { icon: <SyncOutlined />, title: '系统状态', lines: ['运行正常', '版本号：v2.1.0'], tone: 'green' },
  ]
}

function timeRange(start: string, end: string) {
  return `${start}  -  ${end}`
}

function formatLogTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

export function AdminSettingsPanel({ onOpenProfile }: AdminSettingsPanelProps) {
  const settingsQuery = useQuery({
    queryKey: ['admin-settings'],
    queryFn: adminSettingsApi.get,
    retry: false,
  })
  const [draft, setDraft] = useState<AdminSystemSettings>(defaultSettings)
  const updateMutation = useMutation({
    mutationFn: (body: AdminSystemSettingsUpdateRequest) => adminSettingsApi.update(body),
    onSuccess: (settings) => setDraft(settings),
  })
  const settings = draft
  const overviewCards = buildOverviewCards(settings)

  useEffect(() => {
    if (settingsQuery.data) setDraft(settingsQuery.data)
  }, [settingsQuery.data])

  function patchSettings(patch: AdminSystemSettingsUpdateRequest) {
    const previousDraft = draft
    setDraft((current) => ({ ...current, ...patch }))
    updateMutation.mutate(patch, { onError: () => setDraft(previousDraft) })
  }

  function exportConfig() {
    const config = {
      ...settings,
      serviceTime: timeRange(settings.serviceTimeStart, settings.serviceTimeEnd),
      ticketTime: timeRange(settings.ticketTimeStart, settings.ticketTimeEnd),
      checkInTime: timeRange(settings.checkInTimeStart, settings.checkInTimeEnd),
    }
    const url = URL.createObjectURL(new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'yulong-settings.json'
    document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  }

  return (
    <section className="admin-settings-page">
      <header className="admin-settings-hero">
        <div className="admin-settings-hero-copy">
          <Title level={1}>系统设置</Title>
          <Text>账号安全、通知规则与系统参数配置</Text>
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

      <div className="admin-settings-body">
        {settingsQuery.error ? <Alert showIcon type="warning" message="系统设置暂时无法从后端读取，当前显示默认配置。" /> : null}
        {updateMutation.error ? <Alert showIcon type="error" message="设置保存失败，请稍后重试。" /> : null}
        <div className="admin-settings-overview">
          {overviewCards.map((card) => (
            <section className="admin-settings-overview-card" key={card.title}>
              <span className={`admin-settings-round-icon is-${card.tone}`}>{card.icon}</span>
              <div>
                <strong>{card.title}</strong>
                {card.lines.map((line) => <Text key={line}>{line}</Text>)}
              </div>
              <DownOutlined />
            </section>
          ))}
        </div>

        <div className="admin-settings-grid">
          <section className="admin-settings-card">
            <h2>基础配置</h2>
            <SettingRow label="景区名称">
              <Input value={draft.scenicName} onBlur={() => patchSettings({ scenicName: draft.scenicName })} onChange={(event) => setDraft((current) => ({ ...current, scenicName: event.target.value }))} />
            </SettingRow>
            <SettingRow label="客服时间">
              <TimeRangeInput
                end={draft.serviceTimeEnd}
                onChange={(patch) => setDraft((current) => ({ ...current, ...patch }))}
                onSave={patchSettings}
                start={draft.serviceTimeStart}
                startKey="serviceTimeStart"
                endKey="serviceTimeEnd"
              />
            </SettingRow>
            <SettingRow label="售票时间">
              <TimeRangeInput
                end={draft.ticketTimeEnd}
                onChange={(patch) => setDraft((current) => ({ ...current, ...patch }))}
                onSave={patchSettings}
                start={draft.ticketTimeStart}
                startKey="ticketTimeStart"
                endKey="ticketTimeEnd"
              />
            </SettingRow>
            <SettingRow label="入园时间">
              <TimeRangeInput
                end={draft.checkInTimeEnd}
                onChange={(patch) => setDraft((current) => ({ ...current, ...patch }))}
                onSave={patchSettings}
                start={draft.checkInTimeStart}
                startKey="checkInTimeStart"
                endKey="checkInTimeEnd"
              />
            </SettingRow>
            <SettingRow label="每单限购">
              <div className="admin-settings-limit">
                <InputNumber min={1} max={50} value={draft.perOrderLimit} controls={false} onBlur={() => patchSettings({ perOrderLimit: draft.perOrderLimit })} onChange={(value) => setDraft((current) => ({ ...current, perOrderLimit: value ?? 1 }))} />
                <Text>张（1-50张）</Text>
              </div>
            </SettingRow>
          </section>

          <section className="admin-settings-card">
            <h2>安全设置</h2>
            <SettingRow label="管理员账号">
              <div className="admin-settings-inline-action">
                <Input value="@admin" readOnly />
                <Button onClick={onOpenProfile}>修改密码</Button>
              </div>
            </SettingRow>
            <SettingRow label="会话有效期">
              <div className="admin-settings-limit">
                <InputNumber min={5} max={480} value={draft.sessionTtlMinutes} controls={false} onBlur={() => patchSettings({ sessionTtlMinutes: draft.sessionTtlMinutes })} onChange={(value) => setDraft((current) => ({ ...current, sessionTtlMinutes: value ?? 5 }))} />
                <Text>分钟</Text>
              </div>
            </SettingRow>
            <ToggleRow checked={draft.csrfEnabled} label="CSRF 校验" text="开启后所有请求需携带有效 CSRF Token" onChange={(csrfEnabled) => patchSettings({ csrfEnabled })} />
            <ToggleRow checked={draft.loginGuardEnabled} label="登录保护" text="开启后限制连续错误登录次数" onChange={(loginGuardEnabled) => patchSettings({ loginGuardEnabled })} />
          </section>
        </div>

        <div className="admin-settings-grid">
          <section className="admin-settings-card admin-settings-notice-card">
            <h2>通知配置</h2>
            <ToggleRow checked={draft.smsEnabled} label="短信通知" text="启用后通过短信发送重要通知" onChange={(smsEnabled) => patchSettings({ smsEnabled })} />
            <ToggleRow checked={draft.mailEnabled} label="邮件通知" text="启用后通过邮件发送重要通知" onChange={(mailEnabled) => patchSettings({ mailEnabled })} />
            <ToggleRow checked={draft.refundEnabled} label="退款提醒" text="启用后收到退款时发送提醒" onChange={(refundEnabled) => patchSettings({ refundEnabled })} />
            <ToggleRow checked={draft.stockEnabled} label="库存预警" text="启用后库存不足时发送预警" onChange={(stockEnabled) => patchSettings({ stockEnabled })} />
          </section>

          <section className="admin-settings-card admin-settings-maintenance-card">
            <h2>数据维护</h2>
            <MaintenanceItem action={settings.lastBackupLabel} icon={<CloudDownloadOutlined />} title="备份数据" text="备份数据库与配置文件" />
            <MaintenanceItem action="导出" icon={<ExportOutlined />} title="导出配置" text="导出系统配置到本地" onClick={exportConfig} />
            <MaintenanceItem action="待接入" danger icon={<SyncOutlined />} title="清理缓存" text="清理系统缓存与临时文件" />
            <div className="admin-settings-retention">
              <CalendarOutlined />
              <div>
                <strong>审计保留天数</strong>
                <Text>保留审计日志的天数</Text>
              </div>
              <InputNumber min={30} max={365} value={draft.auditRetentionDays} controls={false} onBlur={() => patchSettings({ auditRetentionDays: draft.auditRetentionDays })} onChange={(value) => setDraft((current) => ({ ...current, auditRetentionDays: value ?? 30 }))} />
              <Text>天</Text>
            </div>
          </section>
        </div>

        <section className="admin-settings-card admin-settings-log-card">
          <div className="admin-settings-card-head">
            <h2>系统日志摘要</h2>
            <span>最近 3 条 <DownOutlined /></span>
          </div>
          <table>
            <thead>
              <tr><th>时间</th><th>操作人</th><th>操作内容</th><th>来源 IP</th></tr>
            </thead>
            <tbody>
              {(settings.recentLogs.length ? settings.recentLogs : defaultSettings.recentLogs).map((row) => (
                <tr key={`${row.createdAt}-${row.action}`}>
                  <td>{formatLogTime(row.createdAt)}</td>
                  <td>{row.operatorDisplayName}（@{row.operatorUsername}）</td>
                  <td>{row.action}</td>
                  <td>{row.sourceIp ?? '-'}</td>
                </tr>
              ))}
              {!settings.recentLogs.length ? <tr><td colSpan={4}>暂无系统设置变更记录</td></tr> : null}
            </tbody>
          </table>
        </section>
      </div>
    </section>
  )
}

function TimeRangeInput({
  end,
  endKey,
  onChange,
  onSave,
  start,
  startKey,
}: {
  end: string
  endKey: 'serviceTimeEnd' | 'ticketTimeEnd' | 'checkInTimeEnd'
  onChange: (patch: AdminSystemSettingsUpdateRequest) => void
  onSave: (patch: AdminSystemSettingsUpdateRequest) => void
  start: string
  startKey: 'serviceTimeStart' | 'ticketTimeStart' | 'checkInTimeStart'
}) {
  return (
    <div className="admin-settings-time-range">
      <Input type="time" value={start} onBlur={() => onSave({ [startKey]: start })} onChange={(event) => onChange({ [startKey]: event.target.value })} />
      <span>-</span>
      <Input type="time" value={end} onBlur={() => onSave({ [endKey]: end })} onChange={(event) => onChange({ [endKey]: event.target.value })} />
    </div>
  )
}

function SettingRow({ children, label }: { children: ReactNode; label: string }) {
  return (
    <label className="admin-settings-row">
      <span>{label}</span>
      {children}
    </label>
  )
}

function ToggleRow({ checked, label, onChange, text }: { checked: boolean; label: string; onChange: (checked: boolean) => void; text: string }) {
  return (
    <div className="admin-settings-toggle-row">
      <div>
        <strong>{label}</strong>
        <Text>{text}</Text>
      </div>
      <Switch checked={checked} onChange={onChange} />
    </div>
  )
}

function MaintenanceItem({
  action,
  danger,
  icon,
  onClick,
  text,
  title,
}: {
  action: string
  danger?: boolean
  icon: ReactNode
  onClick?: () => void
  text: string
  title: string
}) {
  return (
    <div className={`admin-settings-maintenance-item${danger ? ' is-danger' : ''}`}>
      <span>{icon}</span>
      <div>
        <strong>{title}</strong>
        <Text>{text}</Text>
      </div>
      {onClick ? <Button onClick={onClick}>{action}</Button> : <em>{action}</em>}
    </div>
  )
}
