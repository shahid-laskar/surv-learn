/**
 * lib/auth.ts
 * Lightweight permission/role helpers that read from localStorage.
 * Stored by Login.tsx on successful authentication.
 */

export const getPermissions = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem('permissions') ?? '[]')
  } catch {
    return []
  }
}

export const getRoles = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem('roles') ?? '[]')
  } catch {
    return []
  }
}

export const getUserType = (): string =>
  localStorage.getItem('user_type') ?? 'EMPLOYEE'

export const hasPermission = (perm: string): boolean =>
  getPermissions().includes(perm)

export const hasRole = (role: string): boolean =>
  getRoles().includes(role)

/** True if the user has the SUPER_ADMIN role (all-access). */
export const isSuperAdmin = (): boolean => hasRole('SUPER_ADMIN')

/** Clear all auth-related keys from localStorage. */
export const clearAuthStorage = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  localStorage.removeItem('roles')
  localStorage.removeItem('permissions')
  localStorage.removeItem('user_type')
}
