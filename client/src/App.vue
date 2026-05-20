<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed, 'sidebar-hidden': isMobileHidden }">

    <!-- Mobile hamburger -->
    <button class="hamburger-btn" @click="openMobileSidebar" aria-label="Open navigation">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="6" x2="21" y2="6" />
        <line x1="3" y1="12" x2="21" y2="12" />
        <line x1="3" y1="18" x2="21" y2="18" />
      </svg>
    </button>

    <!-- Mobile overlay -->
    <div class="sidebar-overlay" :class="{ visible: isMobileOpen }" @click="closeMobileSidebar"></div>

    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'mobile-open': isMobileOpen }">

      <!-- Sidebar header: logo -->
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <path d="M8 21h8M12 17v4" />
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-name">{{ t('nav.companyName') }}</span>
            <span class="logo-subtitle">{{ t('nav.subtitle') }}</span>
          </div>
        </div>
        <button class="toggle-btn" @click="toggleSidebar" :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline v-if="!isCollapsed" points="15 18 9 12 15 6" />
            <polyline v-else points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      <!-- Navigation links -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="{ active: isActive(item.to) }"
          :title="isCollapsed ? item.label : ''"
          @click="closeMobileSidebar"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Sidebar footer: language + profile -->
      <div class="sidebar-footer">
        <div class="footer-controls">
          <LanguageSwitcher />
        </div>
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <!-- Main area -->
    <div class="main-area">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

const STORAGE_KEY = 'sidebar_collapsed'

const ICON_OVERVIEW = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`
const ICON_INVENTORY = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>`
const ICON_ORDERS = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1" ry="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>`
const ICON_FINANCE = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`
const ICON_DEMAND = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`
const ICON_REPORTS = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`
const ICON_RESTOCKING = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>`

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const route = useRoute()
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Sidebar state
    const savedCollapsed = localStorage.getItem(STORAGE_KEY)
    const isMobile = () => window.innerWidth < 768
    const isTablet = () => window.innerWidth < 1024

    // Default: collapsed on < 1024px, expanded on >= 1024px
    const isCollapsed = ref(
      savedCollapsed !== null
        ? savedCollapsed === 'true'
        : isTablet()
    )
    const isMobileHidden = ref(isMobile())
    const isMobileOpen = ref(false)

    const toggleSidebar = () => {
      isCollapsed.value = !isCollapsed.value
      localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
    }

    const openMobileSidebar = () => {
      isMobileOpen.value = true
    }

    const closeMobileSidebar = () => {
      isMobileOpen.value = false
    }

    const handleResize = () => {
      const mobile = isMobile()
      isMobileHidden.value = mobile
      if (!mobile && isMobileOpen.value) {
        isMobileOpen.value = false
      }
    }

    onMounted(() => window.addEventListener('resize', handleResize))
    onUnmounted(() => window.removeEventListener('resize', handleResize))

    const navItems = computed(() => [
      { to: '/',           label: t('nav.overview'),        icon: ICON_OVERVIEW   },
      { to: '/inventory',  label: t('nav.inventory'),       icon: ICON_INVENTORY  },
      { to: '/orders',     label: t('nav.orders'),          icon: ICON_ORDERS     },
      { to: '/spending',   label: t('nav.finance'),         icon: ICON_FINANCE    },
      { to: '/demand',     label: t('nav.demandForecast'),  icon: ICON_DEMAND     },
      { to: '/reports',    label: 'Reports',                icon: ICON_REPORTS    },
      { to: '/restocking', label: 'Restocking',             icon: ICON_RESTOCKING },
    ])

    // Exact match for root, prefix match for others
    const isActive = (path) => {
      if (path === '/') return route.path === '/'
      return route.path.startsWith(path)
    }

    // Tasks
    const tasks = computed(() => [...currentUser.value.tasks, ...apiTasks.value])

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)
        if (isMockTask) {
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) currentUser.value.tasks.splice(index, 1)
        } else {
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)
        if (mockTask) {
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) apiTasks.value[index] = updatedTask
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      isCollapsed,
      isMobileHidden,
      isMobileOpen,
      toggleSidebar,
      openMobileSidebar,
      closeMobileSidebar,
      navItems,
      isActive,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ── Reset ─────────────────────────────────────────────────── */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f8fafc;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── App layout ─────────────────────────────────────────────── */
.app {
  display: flex;
  min-height: 100vh;
}

/* ── Sidebar ────────────────────────────────────────────────── */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 220px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  z-index: 200;
  transition: width 0.22s ease, transform 0.22s ease;
  overflow: hidden;
}

.app.sidebar-collapsed .sidebar {
  width: 64px;
}

/* ── Sidebar header ──────────────────────────────────────────── */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.75rem;
  height: 64px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  overflow: hidden;
}

.logo-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: #eff6ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
}

.logo-icon svg {
  width: 18px;
  height: 18px;
}

.logo-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: opacity 0.18s ease, width 0.22s ease;
}

.logo-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logo-subtitle {
  font-size: 0.7rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app.sidebar-collapsed .logo-text {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

.toggle-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: background 0.15s ease, color 0.15s ease;
}

.toggle-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.toggle-btn svg {
  width: 14px;
  height: 14px;
}

.app.sidebar-collapsed .toggle-btn {
  /* Keep toggle visible and centered when collapsed */
  margin: 0 auto;
}

/* ── Nav links ─────────────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.625rem;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease;
  position: relative;
}

.sidebar-nav a:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.sidebar-nav a.active {
  background: #eff6ff;
  color: #2563eb;
}

.nav-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
  transition: opacity 0.18s ease, width 0.22s ease;
}

.app.sidebar-collapsed .nav-label {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

/* ── Sidebar footer ──────────────────────────────────────────── */
.sidebar-footer {
  border-top: 1px solid #e2e8f0;
  padding: 0.625rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-shrink: 0;
}

.footer-controls {
  display: flex;
  justify-content: center;
}

.app.sidebar-collapsed .footer-controls {
  justify-content: center;
}

/* ── Main area ──────────────────────────────────────────────── */
.main-area {
  flex: 1;
  min-width: 0;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.22s ease;
}

.app.sidebar-collapsed .main-area {
  margin-left: 64px;
}

.main-content {
  flex: 1;
  padding: 1.5rem 2rem;
  max-width: 1600px;
  width: 100%;
}

/* ── Mobile: hamburger ──────────────────────────────────────── */
.hamburger-btn {
  display: none;
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: 300;
  width: 40px;
  height: 40px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  color: #0f172a;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.hamburger-btn svg {
  width: 18px;
  height: 18px;
}

/* ── Mobile: overlay ────────────────────────────────────────── */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  z-index: 190;
}

/* ── Responsive ─────────────────────────────────────────────── */
@media (max-width: 767px) {
  .hamburger-btn {
    display: flex;
  }

  .sidebar {
    transform: translateX(-100%);
    width: 220px !important; /* always full width when open on mobile */
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  /* overlay visibility controlled by .visible class bound in template */

  .main-area {
    margin-left: 0 !important;
    padding-top: 64px; /* space for hamburger */
  }

  .main-content {
    padding: 1rem;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  /* Tablet: sidebar visible but collapsed by default */
  .app.sidebar-collapsed .sidebar {
    width: 64px;
  }

  .app.sidebar-collapsed .main-area {
    margin-left: 64px;
  }
}

/* ── Tooltip for collapsed icons ──────────────────────────────── */
.app.sidebar-collapsed .sidebar-nav a[title]:hover::after {
  content: attr(title);
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  background: #0f172a;
  color: #f8fafc;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
  white-space: nowrap;
  pointer-events: none;
  z-index: 400;
}

/* ── Global component styles (tables, cards, badges, etc.) ───── */

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: #059669; }
.stat-card.danger  .stat-value { color: #dc2626; }
.stat-card.info    .stat-value { color: #2563eb; }

.card {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: #f8fafc;
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success    { background: #d1fae5; color: #065f46; }
.badge.warning    { background: #fed7aa; color: #92400e; }
.badge.danger     { background: #fecaca; color: #991b1b; }
.badge.info       { background: #dbeafe; color: #1e40af; }
.badge.increasing { background: #d1fae5; color: #065f46; }
.badge.decreasing { background: #fecaca; color: #991b1b; }
.badge.stable     { background: #e0e7ff; color: #3730a3; }
.badge.high       { background: #fecaca; color: #991b1b; }
.badge.medium     { background: #fed7aa; color: #92400e; }
.badge.low        { background: #dbeafe; color: #1e40af; }

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
