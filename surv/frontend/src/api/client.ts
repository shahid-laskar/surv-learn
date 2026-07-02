import axios from 'axios'

// All traffic now goes through Kong on :8000, which proxies /api → FastAPI
// and /hls → nginx_hls. No more direct :8000 (FastAPI) or :8080 (nginx_hls)
// access from the browser.
const BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

const api = axios.create({
  baseURL: BASE,
  timeout: 15_000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear stale token and bounce to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('roles')
      localStorage.removeItem('permissions')
      localStorage.removeItem('user_type')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ── Existing types ─────────────────────────────────────────

export interface Camera {
  id:            number
  cam_id:        string
  cam_name:      string | null
  cam_ip:        string
  cam_port:      number
  onvif_port?:   number | null
  rtsp_url?:     string | null
  onvif_username?: string | null
  onvif_password?: string | null
  is_active:     boolean
  is_online:     boolean
  motion_active: boolean
  last_seen:     string | null
  created_at:    string
  organization_id?: number | null
  customer_id?: number | null
}

export interface CameraCreate {
  cam_id:         string
  cam_name?:      string
  cam_ip:         string
  cam_port?:      number
  onvif_port?:    number
  rtsp_url?:      string
  onvif_username?: string
  onvif_password?: string
  motion_active?: boolean
  organization_id?: number
  customer_id?:     number
}

export interface MotionEvent {
  id:           number
  camera_id:    number
  motion_start: string
  motion_end:   string | null
  is_active:    boolean
  created_at:   string
}

export interface Segment {
  segment_id:       number
  start:            string
  end:              string | null
  duration_seconds: number | null
  playback_url:     string
}

export interface Timeline {
  camera_id:      string
  date:           string
  total_segments: number
  segments:       Segment[]
}

export interface StreamTokenResponse {
  cam_id:     string
  hls_url:    string
  token:      string
  expires_at: string
}

// ── Updated auth types (new RBAC fields) ──────────────────

export interface LoginResponse {
  access_token: string
  token_type:   string
  expires_in:   number
  username:     string
  // Legacy flat role (backward-compat)
  role:         string
  // New RBAC fields
  user_type:    string
  roles:        string[]
  permissions:  string[]
  org_id:       number | null
  customer_id:  number | null
}

export interface CurrentUser {
  id:              number
  username:        string
  email:           string | null
  mobile:          string | null
  first_name:      string | null
  last_name:       string | null
  full_name:       string | null
  user_type:       string
  role:            string
  is_active:       boolean
  is_locked:       boolean
  organization_id: number | null
  customer_id:     number | null
  circle_id:       number | null
  ba_id:           number | null
  last_login:      string | null
  created_at:      string
  roles:           string[]
  permissions:     string[]
}

export interface UserCreate {
  username:        string
  password:        string
  email?:          string
  mobile?:         string
  first_name?:     string
  last_name?:      string
  full_name?:      string
  user_type?:      string
  role?:           string
  organization_id?: number
  customer_id?:    number
  circle_id?:      number
  ba_id?:          number
}

// ── Organization types ─────────────────────────────────────

export type OrgType = 'ROOT' | 'CIRCLE' | 'BA' | 'SSA' | 'DISTRICT' | 'SITE' | 'NOC'

export interface Organization {
  id:        number
  parent_id: number | null
  code:      string
  name:      string
  type:      OrgType
  circle_id: number | null
  ba_id:     number | null
  is_active: boolean
  created_at: string
}

export interface OrganizationCreate {
  parent_id?: number
  code:       string
  name:       string
  type:       OrgType
  circle_id?: number
  ba_id?:     number
}

// ── BSNL Master types ──────────────────────────────────────

export interface CircleMaster {
  id:         number
  cir_code:   string
  cir_name:   string
  is_active:  boolean
  created_at: string
}

export interface BAMaster {
  id:         number
  ba_code:    string
  ba_name:    string
  circle_id:  number
  is_active:  boolean
  created_at: string
}

// ── Customer types ─────────────────────────────────────────

export type CustomerType = 'ENTERPRISE' | 'BANK' | 'SCHOOL' | 'HOSPITAL' | 'APARTMENT' | 'GOVERNMENT' | 'INDIVIDUAL' | 'PARTNER'

export interface Customer {
  id:                 number
  parent_customer_id: number | null
  customer_code:      string | null
  name:               string
  customer_type:      CustomerType | null
  organization_id:    number | null
  circle_id:          number | null
  ba_id:              number | null
  email:              string | null
  phone:              string | null
  is_active:          boolean
  created_at:         string
}

export interface CustomerCreate {
  parent_customer_id?: number
  customer_code?:      string
  name:                string
  customer_type?:      CustomerType
  organization_id?:    number
  circle_id?:          number
  ba_id?:              number
  email?:              string
  phone?:              string
  address?:            string
}

export interface CustomerSite {
  id:          number
  customer_id: number
  site_code:   string | null
  name:        string | null
  state:       string | null
  district:    string | null
  city:        string | null
  latitude:    number | null
  longitude:   number | null
  is_active:   boolean
  created_at:  string
}

export interface CustomerSiteCreate {
  site_code?: string
  name?:      string
  state?:     string
  district?:  string
  city?:      string
  address?:   string
  latitude?:  number
  longitude?: number
}

// ── RBAC types ─────────────────────────────────────────────

export interface Role {
  id:          number
  code:        string
  name:        string | null
  description: string | null
}

export interface RoleCreate {
  code:        string
  name?:       string
  description?: string
}

export interface Permission {
  id:          number
  code:        string
  name:        string | null
  description: string | null
}

export interface PermissionCreate {
  code:        string
  name?:       string
  description?: string
}

// ── Camera Group types ─────────────────────────────────────

export interface CameraGroup {
  id:              number
  name:            string
  organization_id: number | null
  customer_id:     number | null
}

export interface CameraGroupCreate {
  name:             string
  organization_id?: number
  customer_id?:     number
}

// ── Audit Log types ────────────────────────────────────────

export interface AuditLog {
  id:          number
  user_id:     number | null
  username:    string | null
  action:      string
  entity_type: string | null
  entity_id:   string | null
  old_value:   Record<string, unknown> | null
  new_value:   Record<string, unknown> | null
  ip_address:  string | null
  created_at:  string
}

// ── Auth ───────────────────────────────────────────────────

export const login = (username: string, password: string) =>
  api.post<LoginResponse>('/auth/login', { username, password }).then(r => r.data)

export const fetchMe = () =>
  api.get<CurrentUser>('/auth/me').then(r => r.data)

/** Server-side session revocation + localStorage clear. */
export async function callLogout() {
  try {
    await api.post('/auth/logout')
  } catch {
    // Ignore errors — might already be expired
  } finally {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
    localStorage.removeItem('roles')
    localStorage.removeItem('permissions')
    localStorage.removeItem('user_type')
    window.location.href = '/login'
  }
}

/** Legacy client-only logout (kept for imports that haven't migrated). */
export function logout() {
  callLogout()
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem('token')
}

// ── Users ──────────────────────────────────────────────────

export const fetchUsers = () =>
  api.get<CurrentUser[]>('/auth/users').then(r => r.data)

export const createUser = (payload: UserCreate) =>
  api.post<CurrentUser>('/auth/users', payload).then(r => r.data)

export const assignRoleToUser = (userId: number, roleId: number) =>
  api.post(`/users/${userId}/roles`, { role_id: roleId })

export const removeRoleFromUser = (userId: number, roleId: number) =>
  api.delete(`/users/${userId}/roles/${roleId}`)

// ── Cameras ────────────────────────────────────────────────

export const fetchCameras   = () =>
  api.get<Camera[]>('/cameras/').then(r => r.data)

export const fetchCamera    = (camId: string) =>
  api.get<Camera>(`/cameras/${camId}`).then(r => r.data)

export const createCamera   = (payload: CameraCreate) =>
  api.post<Camera>('/cameras/', payload).then(r => r.data)

export const updateCamera   = (camId: string, payload: Partial<CameraCreate & { is_active: boolean }>) =>
  api.patch<Camera>(`/cameras/${camId}`, payload).then(r => r.data)

export const deleteCamera   = (camId: string) =>
  api.delete(`/cameras/${camId}`)

// ── Streams ────────────────────────────────────────────────

export const fetchHlsUrl = (camId: string) =>
  api.get<StreamTokenResponse>(`/streams/${camId}/hls-url`).then(r => r.data)

// ── Motion ─────────────────────────────────────────────────

export const fetchMotionEvents = (params?: {
  camera_id?: number
  active?:    boolean
  limit?:     number
}) => api.get<MotionEvent[]>('/motion/', { params }).then(r => r.data)

export const fetchActiveMotion = () =>
  api.get<MotionEvent[]>('/motion/active').then(r => r.data)

// ── Recordings ─────────────────────────────────────────────

export const fetchTimeline  = (camId: string, date: string) =>
  api.get<Timeline>(`/recordings/${camId}/timeline`, { params: { date } }).then(r => r.data)

export const fetchServiceHealth = () =>
  api.get('/health/services').then(r => r.data)

// ── Organizations ──────────────────────────────────────────

export const fetchOrgs = () =>
  api.get<Organization[]>('/org/').then(r => r.data)

export const createOrg = (payload: OrganizationCreate) =>
  api.post<Organization>('/org/', payload).then(r => r.data)

export const fetchOrg = (orgId: number) =>
  api.get<Organization>(`/org/${orgId}`).then(r => r.data)

export const fetchSubtree = (orgId: number) =>
  api.get<Organization[]>(`/org/${orgId}/subtree`).then(r => r.data)

export const updateOrg = (orgId: number, payload: Partial<OrganizationCreate & { is_active: boolean }>) =>
  api.patch<Organization>(`/org/${orgId}`, payload).then(r => r.data)

// ── BSNL Masters ───────────────────────────────────────────

export const fetchCircles = () =>
  api.get<CircleMaster[]>('/bsnl/circles').then(r => r.data)

export const fetchBAs = (circleId?: number) =>
  api.get<BAMaster[]>('/bsnl/bas', { params: circleId ? { circle_id: circleId } : {} }).then(r => r.data)

// ── Customers ──────────────────────────────────────────────

export const fetchCustomers = () =>
  api.get<Customer[]>('/customers/').then(r => r.data)

export const createCustomer = (payload: CustomerCreate) =>
  api.post<Customer>('/customers/', payload).then(r => r.data)

export const fetchCustomer = (customerId: number) =>
  api.get<Customer>(`/customers/${customerId}`).then(r => r.data)

export const updateCustomer = (customerId: number, payload: Partial<CustomerCreate & { is_active: boolean }>) =>
  api.patch<Customer>(`/customers/${customerId}`, payload).then(r => r.data)

export const fetchCustomerSites = (customerId: number) =>
  api.get<CustomerSite[]>(`/customers/${customerId}/sites`).then(r => r.data)

export const createCustomerSite = (customerId: number, payload: CustomerSiteCreate) =>
  api.post<CustomerSite>(`/customers/${customerId}/sites`, payload).then(r => r.data)

// ── Roles & Permissions ────────────────────────────────────

export const fetchRoles = () =>
  api.get<Role[]>('/roles/').then(r => r.data)

export const createRole = (payload: RoleCreate) =>
  api.post<Role>('/roles/', payload).then(r => r.data)

export const fetchPermissions = () =>
  api.get<Permission[]>('/permissions/').then(r => r.data)

export const createPermission = (payload: PermissionCreate) =>
  api.post<Permission>('/permissions/', payload).then(r => r.data)

export const fetchRolePermissions = (roleId: number) =>
  api.get<Permission[]>(`/roles/${roleId}/permissions`).then(r => r.data)

export const assignPermissionToRole = (roleId: number, permissionId: number) =>
  api.post(`/roles/${roleId}/permissions`, { permission_id: permissionId })

export const removePermissionFromRole = (roleId: number, permId: number) =>
  api.delete(`/roles/${roleId}/permissions/${permId}`)

// ── Camera Groups ──────────────────────────────────────────

export const fetchCameraGroups = () =>
  api.get<CameraGroup[]>('/camera-groups/').then(r => r.data)

export const createCameraGroup = (payload: CameraGroupCreate) =>
  api.post<CameraGroup>('/camera-groups/', payload).then(r => r.data)

export const fetchCameraGroup = (groupId: number) =>
  api.get<CameraGroup>(`/camera-groups/${groupId}`).then(r => r.data)

export const addCameraToGroup = (groupId: number, cameraId: number) =>
  api.post(`/camera-groups/${groupId}/cameras`, { camera_id: cameraId })

export const removeCameraFromGroup = (groupId: number, cameraId: number) =>
  api.delete(`/camera-groups/${groupId}/cameras/${cameraId}`)

// ── Audit Logs ─────────────────────────────────────────────

export const fetchAuditLogs = (params?: {
  entity_type?: string
  entity_id?:   string
  user_id?:     number
  action?:      string
  limit?:       number
  offset?:      number
}) => api.get<AuditLog[]>('/audit/', { params }).then(r => r.data)

export default api
