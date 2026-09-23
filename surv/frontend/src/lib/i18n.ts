/**
 * lib/i18n.ts
 * Bilingual localization (English / Malayalam) for SARVANETRA Command Platform.
 * Supports hot language switching without page breakage across all platform domains:
 * Navigation, ICCC, Video Wall, Parking Management, ANPR, Alerts, and System Health.
 */

import { create } from 'zustand'

export type Language = 'en' | 'ml'

export const TRANSLATIONS = {
  en: {
    // Navigation
    nav_live_view: 'Live View',
    nav_playback: 'Playback',
    nav_motion_alerts: 'Motion Alerts',
    nav_cameras: 'Cameras',
    nav_iccc: 'ICCC Command GIS',
    nav_parking: 'Parking (Nilakkal)',
    nav_anpr: 'ANPR & Hotlist',
    nav_health: 'Health',
    nav_camera_groups: 'Camera Groups',
    nav_fleet: 'NVR Fleet',
    nav_org: 'Organizations',
    nav_customers: 'Customers',
    nav_users: 'Users',
    nav_roles: 'Roles & Perms',
    nav_audit: 'Audit Log',
    nav_logout: 'Sign out',

    // System Header
    system_nominal: 'System nominal',
    realtime_connected: 'Realtime · connected',
    switch_language: 'മലയാളം',

    // ICCC Common Operating Picture
    iccc_title: 'Integrated Command & Control Centre (ICCC)',
    iccc_subtitle: 'Real-time Common Operating Picture · Sabarimala & Nilakkal Security Grid',
    iccc_gis_map: 'Geographic Information System (GIS) Map',
    iccc_video_wall: 'Priority Camera Wall',
    iccc_parking_occupancy: 'Parking Grounds Occupancy',
    iccc_anpr_alerts: 'ANPR Interception Alerts',
    iccc_system_health: 'Command Health & Edge Nodes',
    iccc_all_cameras: 'All Cameras',
    iccc_online_cameras: 'Online',
    iccc_offline_cameras: 'Offline',
    iccc_critical_alerts: 'Critical Hits',
    iccc_total_slots: 'Total Capacity',
    iccc_occupied_slots: 'Occupied',
    iccc_available_slots: 'Available',

    // Parking Management
    pms_title: 'Sabarimala Nilakkal Parking Management',
    pms_subtitle: 'Zone Allocation, Automated Boom Barrier, Handheld POS Slips & Occupancy',
    pms_new_entry: 'Vehicle Entry Allocation',
    pms_process_exit: 'Process Vehicle Exit',
    pms_zone: 'Zone / Ground',
    pms_plate: 'Vehicle Number',
    pms_type: 'Vehicle Type',
    pms_capacity: 'Capacity',
    pms_occupancy: 'Occupancy',
    pms_vacancy: 'Vacancy',
    pms_slip_no: 'Slip No',
    pms_fee: 'Fee (₹)',
    pms_allocate_btn: 'Allocate Slot & Issue Slip',
    pms_exit_btn: 'Calculate Fee & Complete Exit',

    // ANPR & Watchlist
    anpr_title: 'ANPR Management Plane & Hotlist Grid',
    anpr_subtitle: 'Decoupled Optical Plate Reads, Fuzzy Trigram Search & Police Hotlist Alerts',
    anpr_search_placeholder: 'Search plate number (fuzzy match e.g. KL07BH9999)...',
    anpr_live_reads: 'Recent ANPR Detections',
    anpr_watchlist_title: 'Police Watchlist & Wanted Vehicles',
    anpr_add_watchlist: 'Register Hotlist Vehicle',
    anpr_confidence: 'Confidence',
    anpr_source: 'Processing Node',
    anpr_corrected: 'Operator Corrected',
    anpr_correct_btn: 'Correct Plate',
    anpr_ack_btn: 'Acknowledge Interception',

    // Generic
    status_active: 'ACTIVE',
    status_completed: 'COMPLETED',
    status_acknowledged: 'ACKNOWLEDGED',
    filter_all: 'All',
    close: 'Close',
    refresh: 'Refresh',
    submit: 'Submit',
    cancel: 'Cancel',
  },
  ml: {
    // Navigation
    nav_live_view: 'തത്സമയ ദൃശ്യങ്ങൾ',
    nav_playback: 'റെക്കോർഡിംഗ് പ്ലേബാക്ക്',
    nav_motion_alerts: 'ചലന അറിയിപ്പുകൾ',
    nav_cameras: 'ക്യാമറകൾ',
    nav_iccc: 'ഐ.സി.സി.സി കമാൻഡ് ജി.ഐ.എസ്',
    nav_parking: 'പാർക്കിംഗ് മാനേജ്‌മെന്റ് (നിലയ്ക്കൽ)',
    nav_anpr: 'നമ്പർ പ്ലേറ്റ് & വാച്ച്‌ലിസ്റ്റ്',
    nav_health: 'സിസ്റ്റം ആരോഗ്യം',
    nav_camera_groups: 'ക്യാമറ ഗ്രൂപ്പുകൾ',
    nav_fleet: 'എൻ.വി.ആർ ഫ്ലീറ്റ്',
    nav_org: 'ഓർഗനൈസേഷനുകൾ',
    nav_customers: 'ഉപഭോക്താക്കൾ',
    nav_users: 'ഉപയോക്താക്കൾ',
    nav_roles: 'പദവികളും അനുമതികളും',
    nav_audit: 'ഓഡിറ്റ് ലോഗ്',
    nav_logout: 'ലോഗൗട്ട്',

    // System Header
    system_nominal: 'സിസ്റ്റം സാധാരണ നിലയിൽ',
    realtime_connected: 'തത്സമയം · കണക്റ്റ് ചെയ്തു',
    switch_language: 'English',

    // ICCC Common Operating Picture
    iccc_title: 'സംയോജിത കമാൻഡ് ആൻഡ് കൺട്രോൾ സെന്റർ (ICCC)',
    iccc_subtitle: 'തത്സമയ പ്രവർത്തന ചിത്രം · ശബരിമല - നിലയ്ക്കൽ സുരക്ഷാ ഗ്രിഡ്',
    iccc_gis_map: 'ഭൂമിശാസ്ത്ര മാപ്പ് (GIS)',
    iccc_video_wall: 'പ്രധാന ക്യാമറ വാൾ',
    iccc_parking_occupancy: 'നിലയ്ക്കൽ ഗ്രൗണ്ട് പാർക്കിംഗ് നില',
    iccc_anpr_alerts: 'വാഹന മുന്നറിയിപ്പുകൾ (ANPR Alerts)',
    iccc_system_health: 'കൺട്രോൾ റൂം ആരോഗ്യം & എഡ്ജ് നോഡുകൾ',
    iccc_all_cameras: 'ആകെ ക്യാമറകൾ',
    iccc_online_cameras: 'ഓൺലൈൻ',
    iccc_offline_cameras: 'ഓഫ്‌ലൈൻ',
    iccc_critical_alerts: 'അടിയന്തിര മുന്നറിയിപ്പുകൾ',
    iccc_total_slots: 'ആകെ സ്ഥലം',
    iccc_occupied_slots: 'പാർക്ക് ചെയ്തവ',
    iccc_available_slots: 'ലഭ്യമായ സ്ഥലം',

    // Parking Management
    pms_title: 'ശബരിമല നിലയ്ക്കൽ പാർക്കിംഗ് മാനേജ്‌മെന്റ്',
    pms_subtitle: 'ഗ്രൗണ്ട് അനുമതി, ഓട്ടോമേറ്റഡ് ബാരിയർ, തെർമൽ സ്ലിപ്പ് & തത്സമയ നില',
    pms_new_entry: 'വാഹന പ്രവേശന അനുമതി',
    pms_process_exit: 'വാഹന നിർഗ്ഗമനം & ഫീസ്',
    pms_zone: 'പാർക്കിംഗ് ഗ്രൗണ്ട്',
    pms_plate: 'വാഹന നമ്പർ',
    pms_type: 'വാഹന വിഭാഗം',
    pms_capacity: 'ശേഷി',
    pms_occupancy: 'ഉപയോഗത്തിലുള്ളവ',
    pms_vacancy: 'ബാക്കിയുള്ളവ',
    pms_slip_no: 'സ്ലിപ്പ് നമ്പർ',
    pms_fee: 'ഫീസ് (₹)',
    pms_allocate_btn: 'സ്ഥലം അനുവദിച്ച് സ്ലിപ്പ് നൽകുക',
    pms_exit_btn: 'ഫീസ് ഈടാക്കി വിടുക',

    // ANPR & Watchlist
    anpr_title: 'നമ്പർ പ്ലേറ്റ് നിരീക്ഷണവും പോലീസ് വാച്ച്‌ലിസ്റ്റും',
    anpr_subtitle: 'വാഹന നമ്പർ തിരിച്ചറിയൽ, അവ്യക്ത തിരച്ചിൽ & പോലീസ് വാച്ച്‌ലിസ്റ്റ് അലേർട്ട്',
    anpr_search_placeholder: 'വാഹന നമ്പർ തിരയുക (ഉദാ: KL07BH9999)...',
    anpr_live_reads: 'പുതിയ വാഹന റീഡിംഗുകൾ',
    anpr_watchlist_title: 'പോലീസ് വാച്ച്‌ലിസ്റ്റ് വാഹനങ്ങൾ',
    anpr_add_watchlist: 'പുതിയ വാച്ച്‌ലിസ്റ്റ് വാഹനം ചേർക്കുക',
    anpr_confidence: 'കൃത്യത (Confidence)',
    anpr_source: 'പ്രോസസ്സിംഗ് നോഡ്',
    anpr_corrected: 'തിരുത്തിയത്',
    anpr_correct_btn: 'നമ്പർ തിരുത്തുക',
    anpr_ack_btn: 'നടപടി സ്വീകരിച്ചതായി രേഖപ്പെടുത്തുക',

    // Generic
    status_active: 'സജീവം',
    status_completed: 'പൂർത്തിയായി',
    status_acknowledged: 'പരിശോധിച്ചു',
    filter_all: 'എല്ലാം',
    close: 'അടയ്ക്കുക',
    refresh: 'പുതുക്കുക',
    submit: 'സമർപ്പിക്കുക',
    cancel: 'റദ്ദാക്കുക',
  },
} as const

export type TranslationKey = keyof typeof TRANSLATIONS['en']

interface I18nStore {
  language: Language
  setLanguage: (lang: Language) => void
  toggleLanguage: () => void
  t: (key: TranslationKey) => string
}

export const useI18n = create<I18nStore>((set, get) => ({
  language: (localStorage.getItem('sarvanetra_language') as Language) || 'en',
  setLanguage: (lang: Language) => {
    localStorage.setItem('sarvanetra_language', lang)
    set({ language: lang })
  },
  toggleLanguage: () => {
    const nextLang: Language = get().language === 'en' ? 'ml' : 'en'
    localStorage.setItem('sarvanetra_language', nextLang)
    set({ language: nextLang })
  },
  t: (key: TranslationKey) => {
    const lang = get().language
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['en'][key] || key
  },
}))
