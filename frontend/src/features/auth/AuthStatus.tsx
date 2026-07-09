import { Form } from 'antd'
import { useEffect, useState } from 'react'
import { AuthDialog } from './components/AuthDialog'
import { AuthSessionStatus } from './components/AuthSessionStatus'
import {
  useVisitorLoginMutation,
  useVisitorLogoutMutation,
  useVisitorRegisterMutation,
  useVisitorSessionQuery,
} from './queries'
import type { AuthMode, LoginFormValues, RegisterFormValues } from './types'
import { normalizePhone } from './utils'

export type { AuthMode } from './types'

type AuthStatusProps = {
  dialogRequest?: {
    mode: AuthMode
    requestId: number
  }
}

export function AuthStatus({ dialogRequest }: AuthStatusProps) {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<AuthMode>('login')
  const [loginForm] = Form.useForm<LoginFormValues>()
  const [registerForm] = Form.useForm<RegisterFormValues>()
  const sessionQuery = useVisitorSessionQuery()
  const loginMutation = useVisitorLoginMutation()
  const registerMutation = useVisitorRegisterMutation()
  const logoutMutation = useVisitorLogoutMutation()
  const visitor = sessionQuery.data ?? null
  const activeError = mode === 'login' ? loginMutation.error : registerMutation.error

  useEffect(() => {
    if (loginMutation.isSuccess || registerMutation.isSuccess) {
      setOpen(false)
      loginForm.resetFields()
      registerForm.resetFields()
    }
  }, [loginForm, loginMutation.isSuccess, registerForm, registerMutation.isSuccess])

  useEffect(() => {
    if (!dialogRequest) {
      return
    }

    setMode(dialogRequest.mode)
    setOpen(true)
  }, [dialogRequest])

  function openLogin() {
    setMode('login')
    setOpen(true)
  }

  function openRegister() {
    setMode('register')
    setOpen(true)
  }

  function submitLogin(values: LoginFormValues) {
    loginMutation.mutate({
      password: values.password,
      username: values.username.trim(),
    })
  }

  function submitRegister(values: RegisterFormValues) {
    registerMutation.mutate({
      password: values.password,
      phone: normalizePhone(values.phone) ?? values.phone,
      username: values.username.trim(),
    })
  }

  return (
    <>
      <AuthSessionStatus
        isLogoutPending={logoutMutation.isPending}
        sessionError={sessionQuery.error}
        isSessionError={sessionQuery.isError}
        isSessionLoading={sessionQuery.isLoading}
        onLogin={openLogin}
        onLogout={() => logoutMutation.mutate()}
        onRegister={openRegister}
        onRetrySession={() => sessionQuery.refetch()}
        visitor={visitor}
      />

      <AuthDialog
        activeError={activeError}
        isLoginPending={loginMutation.isPending}
        isRegisterPending={registerMutation.isPending}
        loginForm={loginForm}
        mode={mode}
        onClose={() => setOpen(false)}
        onLoginSubmit={submitLogin}
        onModeChange={setMode}
        onRegisterSubmit={submitRegister}
        open={open}
        registerForm={registerForm}
      />
    </>
  )
}
