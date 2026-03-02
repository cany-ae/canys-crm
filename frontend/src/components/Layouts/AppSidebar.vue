<template>
  <div
    class="relative flex h-full flex-col justify-between transition-all duration-300 ease-in-out"
    :class="isSidebarCollapsed ? 'w-12' : 'w-[220px]'"
  >
    <div class="p-2">
      <UserDropdown :isCollapsed="isSidebarCollapsed" />
    </div>
    <div class="flex-1 overflow-y-auto">
      <div class="mb-3 flex flex-col">
        <SidebarLink
          id="notifications-btn"
          :label="'Benachrichtigungen'"
          :icon="NotificationsIcon"
          :isCollapsed="isSidebarCollapsed"
          @click="() => toggleNotificationPanel()"
          class="relative mx-2 my-0.5"
        >
          <template #right>
            <Badge
              v-if="!isSidebarCollapsed && unreadNotificationsCount"
              :label="unreadNotificationsCount"
              variant="subtle"
            />
            <div
              v-else-if="unreadNotificationsCount"
              class="absolute -left-1.5 top-1 z-20 h-[5px] w-[5px] translate-x-6 translate-y-1 rounded-full bg-surface-gray-6 ring-1 ring-white"
            />
          </template>
        </SidebarLink>
      </div>
      <div v-for="view in allViews" :key="view.label">
        <div
          v-if="!view.hideLabel && isSidebarCollapsed && view.views?.length"
          class="mx-2 my-2 h-1 border-b"
        />
        <Section
          :label="view.name"
          :hideLabel="view.hideLabel"
          :opened="view.opened"
        >
          <template #header="{ opened, hide, toggle }">
            <div
              v-if="!hide"
              class="flex cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out"
              :class="
                isSidebarCollapsed
                  ? 'ml-0 h-0 overflow-hidden opacity-0'
                  : 'ml-2 mt-4 h-7 w-auto opacity-100'
              "
              @click="toggle()"
            >
              <FeatherIcon
                name="chevron-right"
                class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                :class="{ 'rotate-90': opened }"
              />
              <span>{{ __(view.name) }}</span>
            </div>
          </template>
          <nav class="flex flex-col">
            <template v-for="link in view.views" :key="link.label">
              <SidebarLink
                :icon="link.icon"
                :label="link.label"
                :to="link.to"
                :isCollapsed="isSidebarCollapsed"
                class="mx-2 my-0.5"
                
              >
                <template #right v-if="link.hasQueue && !isSidebarCollapsed">
                  <Badge
                    v-if="queueCounts.total"
                    :label="queueCounts.total"
                    variant="subtle"
                  />
                </template>
              </SidebarLink>
              <!-- Lead Queue sub-items -->
              <div
                v-if="link.hasQueue && !isSidebarCollapsed"
                class="ml-4 mr-2 mb-1 flex flex-col gap-0.5"
              >
                <router-link
                  v-for="phase in leadPhases"
                  :key="phase.value"
                  :to="{ name: 'Leads', query: { phase: phase.value } }"
                  class="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-2 transition-colors cursor-pointer"
                  :class="{ 'bg-surface-gray-2': currentPhaseFilter === phase.value }"
                >
                  <span class="inline-block h-2 w-2 rounded-full flex-shrink-0" :style="{ backgroundColor: phase.hex }"></span>
                  <span class="flex-1 truncate text-xs">{{ phase.short }}</span>
                  <span
                    v-if="queueCounts[phase.value]"
                    class="ml-auto inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold min-w-[20px]"
                    :class="phase.badgeClass"
                  >
                    {{ queueCounts[phase.value] }}
                  </span>
                </router-link>
                <router-link
                  v-if="queueCounts.overdue_followups"
                  :to="{ name: 'Leads', query: { overdue: '1' } }"
                  class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400 mt-0.5 hover:bg-red-100 dark:hover:bg-red-900 cursor-pointer transition-colors"
                >
                  <FeatherIcon name="alert-circle" class="h-3 w-3" />
                  <span>{{ queueCounts.overdue_followups }} überfällig</span>
                </router-link>
                <!-- Spezialisten-Queue -->
                <div
                  v-if="specialistCounts.total > 0"
                  class="mt-2 flex flex-col gap-0.5"
                >
                  <div class="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">
                    <FeatherIcon name="users" class="h-3 w-3" />
                    <span>Spezialisten</span>
                  </div>
                  <router-link
                    :to="{ name: 'Leads', query: { specialist: 'offen' } }"
                    class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-ink-gray-7 hover:bg-surface-gray-2 transition-colors cursor-pointer"
                  >
                    <span class="inline-block h-2 w-2 rounded-full bg-amber-400 flex-shrink-0"></span>
                    <span class="flex-1 truncate">Offen</span>
                    <span v-if="specialistCounts.offen" class="ml-auto inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold min-w-[20px] bg-amber-100 text-amber-700">
                      {{ specialistCounts.offen }}
                    </span>
                  </router-link>
                  <router-link
                    :to="{ name: 'Leads', query: { specialist: 'in_bearbeitung' } }"
                    class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-ink-gray-7 hover:bg-surface-gray-2 transition-colors cursor-pointer"
                  >
                    <span class="inline-block h-2 w-2 rounded-full bg-blue-400 flex-shrink-0"></span>
                    <span class="flex-1 truncate">In Bearbeitung</span>
                    <span v-if="specialistCounts.in_bearbeitung" class="ml-auto inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold min-w-[20px] bg-blue-100 text-blue-700">
                      {{ specialistCounts.in_bearbeitung }}
                    </span>
                  </router-link>
                  <router-link
                    :to="{ name: 'Leads', query: { specialist: 'qualifiziert' } }"
                    class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-ink-gray-7 hover:bg-surface-gray-2 transition-colors cursor-pointer"
                  >
                    <span class="inline-block h-2 w-2 rounded-full bg-green-400 flex-shrink-0"></span>
                    <span class="flex-1 truncate">Qualifiziert</span>
                    <span v-if="specialistCounts.qualifiziert" class="ml-auto inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold min-w-[20px] bg-green-100 text-green-700">
                      {{ specialistCounts.qualifiziert }}
                    </span>
                  </router-link>
                  <router-link
                    v-if="specialistCounts.my_specialist_leads"
                    :to="{ name: 'Leads', query: { specialist: 'mine' } }"
                    class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-purple-600 bg-purple-50 dark:bg-purple-950 dark:text-purple-400 mt-0.5 hover:bg-purple-100 dark:hover:bg-purple-900 cursor-pointer transition-colors"
                  >
                    <FeatherIcon name="user" class="h-3 w-3" />
                    <span>{{ specialistCounts.my_specialist_leads }} meine</span>
                  </router-link>
                </div>
              </div>
            </template>
          </nav>
        </Section>
      </div>
    </div>
    <div class="m-2 flex flex-col gap-0.5">
      <div class="flex flex-col gap-2 mb-1">
        <SignupBanner
          v-if="isDemoSite"
          :isSidebarCollapsed="isSidebarCollapsed"
          :afterSignup="() => capture('signup_from_demo_site')"
        />
        <TrialBanner
          v-if="isFCSite"
          :isSidebarCollapsed="isSidebarCollapsed"
          :afterUpgrade="() => capture('upgrade_plan_from_trial_banner')"
        />
      </div>
      <div class="flex items-center" :class="isSidebarCollapsed ? 'flex-col gap-1' : 'gap-1'">
        <button
          v-if="isOnboardingStepsCompleted"
          @click="() => { showHelpModal = minimize ? true : !showHelpModal; minimize = !showHelpModal; }"
          class="flex items-center justify-center rounded-md text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7 transition-colors"
          :class="isSidebarCollapsed ? 'h-7 w-7' : 'h-7 w-7'"
          :title="__('Hilfe')"
        >
          <HelpIcon class="h-3.5 w-3.5" />
        </button>
        <button
          @click="isSidebarCollapsed = !isSidebarCollapsed"
          class="flex items-center justify-center rounded-md text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7 transition-colors"
          :class="isSidebarCollapsed ? 'h-7 w-7' : 'h-7 w-7'"
          :title="isSidebarCollapsed ? __('Ausklappen') : __('Einklappen')"
        >
          <CollapseSidebar
            class="h-3.5 w-3.5 text-ink-gray-5 duration-300 ease-in-out"
            :class="{ '[transform:rotateY(180deg)]': isSidebarCollapsed }"
          />
        </button>
        <AISidebar :inSidebar="true" :isCollapsed="isSidebarCollapsed" />
      </div>
    </div>
    <Notifications />
    <Settings />
    <HelpModal
      v-if="showHelpModal"
      v-model="showHelpModal"
      v-model:articles="articles"
      :logo="CRMLogo"
      :afterSkip="(step) => capture('onboarding_step_skipped_' + step)"
      :afterSkipAll="() => capture('onboarding_steps_skipped')"
      :afterReset="(step) => capture('onboarding_step_reset_' + step)"
      :afterResetAll="() => capture('onboarding_steps_reset')"
      docsLink="https://docs.frappe.io/crm"
    />
  </div>
</template>

<script setup>
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideTarget from '~icons/lucide/target'
import LucideCoins from '~icons/lucide/coins'
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import Section from '@/components/Section.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LucideArchive from '~icons/lucide/archive'
import UsersIcon from '@/components/Icons/UsersIcon.vue'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import AISidebar from '@/components/AISidebar.vue'
import Notifications from '@/components/Notifications.vue'
import Settings from '@/components/Settings/Settings.vue'
import { viewsStore } from '@/stores/views'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { usePipelinePhases } from '@/composables/usePipelinePhases'
import { showChangePasswordModal } from '@/composables/modals'
import { Badge, FeatherIcon, call } from 'frappe-ui'
import {
  SignupBanner,
  TrialBanner,
  HelpModal,
  useOnboarding,
  showHelpModal,
  minimize,
} from 'frappe-ui/frappe'
import { capture } from '@/telemetry'
import router from '@/router'
import { useStorage } from '@vueuse/core'
import { ref, reactive, computed, h, markRaw, onMounted, onBeforeUnmount } from 'vue'

const { getPinnedViews, getPublicViews } = viewsStore()
const { toggle: toggleNotificationPanel } = notificationsStore()

const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)
const { sidebarPhases } = usePipelinePhases()


const isFCSite = ref(window.is_fc_site)
const isDemoSite = ref(window.is_demo_site)

const links = [
  {
    label: 'Leads',
    icon: LeadsIcon,
    to: 'Leads',
    hasQueue: true,
  },
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    to: 'Dashboard',
  },

  {
    label: 'Deals',
    icon: DealsIcon,
    to: 'Deals',
  },
  {
    label: 'Notizen',
    icon: NoteIcon,
    to: 'Notes',
  },
  {
    label: 'Aufgaben',
    icon: TaskIcon,
    to: 'Tasks',
  },
  {
    label: 'Kalender',
    icon: CalendarIcon,
    to: 'Calendar',
  },
  {
    label: 'Kontakte',
    icon: ContactsIcon,
    to: 'Contacts',
  },
  {
    label: 'Anrufprotokolle',
    icon: PhoneIcon,
    to: 'Call Logs',
  },
  {
    label: 'Archiv',
    icon: LucideArchive,
    to: 'Archive',
  },
]

// Lead Queue Counts
const leadQueueOpen = useStorage('leadQueueOpen', true)
const queueCounts = ref({ total: 0 })
const specialistCounts = ref({ total: 0, offen: 0, in_bearbeitung: 0, qualifiziert: 0, nicht_qualifiziert: 0, my_specialist_leads: 0 })
const currentPhaseFilter = computed(() => {
  const route = router.currentRoute.value
  return route.query?.phase || ''
})

// leadPhases loaded from backend via composable
const leadPhases = sidebarPhases

function toggleLeadQueue() {
  leadQueueOpen.value = !leadQueueOpen.value
}

let queueInterval = null

async function fetchQueueCounts() {
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_lead_queue_counts'
    )
    if (result) {
      queueCounts.value = result
    }
  } catch (e) {
    // silently ignore fetch errors
  }
}

async function fetchSpecialistCounts() {
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_specialist_queue_counts'
    )
    if (result) {
      specialistCounts.value = result
    }
  } catch (e) {
    // silently ignore fetch errors
  }
}

onMounted(() => {
  fetchQueueCounts()
  fetchSpecialistCounts()
  queueInterval = setInterval(() => {
    fetchQueueCounts()
    fetchSpecialistCounts()
  }, 30000)
})

onBeforeUnmount(() => {
  if (queueInterval) clearInterval(queueInterval)
})

const allViews = computed(() => {
  let _views = [
    {
      name: 'All Views',
      hideLabel: true,
      opened: true,
      views: links.filter((link) => {
        if (link.condition) {
          return link.condition()
        }
        return true
      }),
    },
  ]



  return _views
})

function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) return h('div', { class: 'size-auto' }, icon)

  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

// onboarding
const { user } = sessionStore()
const { users } = usersStore()
const { isOnboardingStepsCompleted } = useOnboarding('frappecrm')


onMounted(async () => {
  await users.promise
  // Onboarding-Popup deaktiviert - alle Schritte als erledigt markieren
  isOnboardingStepsCompleted.value = true
})

// help center
const articles = ref([
  {
    title: __('Introduction'),
    opened: false,
    subArticles: [
      { name: 'introduction', title: __('Introduction') },
      { name: 'setting-up', title: __('Setting up') },
    ],
  },
  {
    title: __('Settings'),
    opened: false,
    subArticles: [
      { name: 'profile', title: __('Profile') },
      { name: 'custom-branding', title: __('Custom branding') },
      { name: 'home-actions', title: __('Home actions') },
      { name: 'invite-users', title: __('Invite users') },
    ],
  },
  {
    title: __('Masters'),
    opened: false,
    subArticles: [
      { name: 'lead', title: __('Lead') },
      { name: 'deal', title: __('Deal') },
      { name: 'contact', title: __('Contact') },
      { name: 'organization', title: __('Organization') },
      { name: 'note', title: __('Note') },
      { name: 'task', title: __('Task') },
      { name: 'call-log', title: __('Call log') },
      { name: 'email-template', title: __('Email template') },
    ],
  },
  {
    title: __('Capturing leads'),
    opened: false,
    subArticles: [{ name: 'web-form', title: __('Web form') }],
  },
  {
    title: __('Views'),
    opened: false,
    subArticles: [
      { name: 'view', title: __('Saved view') },
      { name: 'public-view', title: __('Public view') },
      { name: 'pinned-view', title: __('Pinned view') },
    ],
  },
  {
    title: __('Other features'),
    opened: false,
    subArticles: [
      { name: 'email-communication', title: __('Email communication') },
      { name: 'comment', title: __('Comment') },
      { name: 'data', title: __('Data') },
      { name: 'service-level-agreement', title: __('Service level agreement') },
      { name: 'assignment-rule', title: __('Assignment rule') },
      { name: 'notification', title: __('Notification') },
    ],
  },
  {
    title: __('Customization'),
    opened: false,
    subArticles: [
      { name: 'custom-fields', title: __('Custom fields') },
      { name: 'custom-actions', title: __('Custom actions') },
      { name: 'custom-statuses', title: __('Custom statuses') },
      { name: 'custom-list-actions', title: __('Custom list actions') },
      { name: 'quick-entry-layout', title: __('Quick entry layout') },
    ],
  },
  {
    title: __('Integration'),
    opened: false,
    subArticles: [
      { name: 'twilio', title: __('Twilio') },
      { name: 'exotel', title: __('Exotel') },
      { name: 'whatsapp', title: __('WhatsApp') },
      { name: 'erpnext', title: __('ERPNext') },
    ],
  },
  {
    title: __('Frappe CRM mobile'),
    opened: false,
    subArticles: [
      { name: 'mobile-app-installation', title: __('Mobile app installation') },
    ],
  },
])
</script>
