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

// On 401, clear the stale token and bounce to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ── Types ──────────────────────────────────────────────────

export interface Camera {
  id:            number
  cam_id:        string
  cam_name:      string | null
  cam_ip:        string
  cam_port:      number
  is_active:     boolean
  is_online:     boolean
  motion_active: boolean
  last_seen:     string | null
  created_at:    string
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

export interface LoginResponse {
  access_token: string
  token_type:   string
  expires_in:   number
  username:     string
  role:         string
}

export interface CurrentUser {
  id:         number
  username:   string
  full_name:  string | null
  role:       string
  is_active:  boolean
  last_login: string | null
  created_at: string
}

// ── Auth ───────────────────────────────────────────────────

export const login = (username: string, password: string) =>
  api.post<LoginResponse>('/auth/login', { username, password }).then(r => r.data)

export const fetchMe = () =>
  api.get<CurrentUser>('/auth/me').then(r => r.data)

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  window.location.href = '/login'
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem('token')
}

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

// ── Streams (now returns a token-embedded URL) ────────────────────────────

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

export default api
