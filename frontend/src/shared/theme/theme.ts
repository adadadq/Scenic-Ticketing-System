import type { ThemeConfig } from 'antd'

export const appTheme: ThemeConfig = {
  token: {
    colorPrimary: '#008b84',
    colorInfo: '#1677ff',
    colorSuccess: '#2f9e44',
    colorWarning: '#faad14',
    colorError: '#d4380d',
    colorText: '#1f2a37',
    colorTextSecondary: '#5f6b7a',
    colorBorder: '#dce3ea',
    colorBgLayout: '#f5f8fa',
    colorBgContainer: '#ffffff',
    borderRadius: 8,
    borderRadiusLG: 8,
    boxShadowSecondary: '0 10px 30px rgba(18, 38, 63, 0.08)',
    fontFamily:
      '"Avenir Next", "IBM Plex Sans", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
  },
  components: {
    Button: {
      controlHeight: 40,
      primaryShadow: '0 8px 18px rgba(0, 139, 132, 0.22)',
    },
    Card: {
      boxShadowTertiary: '0 8px 24px rgba(18, 38, 63, 0.06)',
    },
    Layout: {
      bodyBg: '#f5f8fa',
      headerBg: '#ffffff',
      siderBg: '#006c69',
    },
    Menu: {
      itemBorderRadius: 8,
      itemSelectedBg: 'rgba(255, 255, 255, 0.14)',
      itemSelectedColor: '#ffffff',
    },
  },
}
