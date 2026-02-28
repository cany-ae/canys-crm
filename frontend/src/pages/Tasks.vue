<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Tasks" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-2">
          <Dropdown
            v-if="isManager && taskUsers.data?.length"
            :options="userFilterOptions"
            placement="right"
          >
            <template #default="{ open }">
              <Button
                :label="activeUserLabel"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
                variant="outline"
                size="sm"
              >
                <template #prefix>
                  <Avatar
                    v-if="activeUser"
                    :label="activeUserLabel"
                    :image="activeUserImage"
                    size="xs"
                  />
                  <FeatherIcon v-else name="users" class="h-3.5 w-3.5" />
                </template>
              </Button>
            </template>
          </Dropdown>
          <Button
            variant="solid"
            label="Erstellen"
            iconLeft="plus"
            @click="openCreateModal"
          />
        </div>
      </template>
    </LayoutHeader>

    <!-- Tabs + Quick Filters -->
    <div class="border-b border-outline-gray-2 bg-surface-white px-3 sm:px-5">
      <!-- View Tabs -->
      <div class="flex items-center gap-1 -mb-px">
        <button
          v-for="tab in visibleTabs"
          :key="tab.value"
          class="relative px-3 py-2.5 text-sm font-medium transition-colors"
          :class="[
            activeView === tab.value
              ? 'text-ink-gray-9 border-b-2 border-ink-gray-9'
              : 'text-ink-gray-5 hover:text-ink-gray-7',
          ]"
          @click="activeView = tab.value"
        >
          <span class="flex items-center gap-1.5">
            {{ tab.label }}
            <span
              v-if="tab.count !== null"
              class="inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-medium min-w-[1.25rem]"
              :class="[
                activeView === tab.value
                  ? 'bg-ink-gray-9 text-white'
                  : 'bg-surface-gray-3 text-ink-gray-6',
              ]"
            >
              {{ tab.count }}
            </span>
          </span>
        </button>
      </div>
    </div>

    <!-- Quick Filter Buttons -->
    <div
      class="flex items-center gap-2 px-3 sm:px-5 py-2.5 border-b border-outline-gray-2 bg-surface-white"
    >
      <button
        v-for="qf in quickFilters"
        :key="qf.value"
        class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium border transition-colors"
        :class="[
          activeQuickFilter === qf.value
            ? 'bg-ink-gray-9 text-white border-ink-gray-9'
            : 'bg-surface-white text-ink-gray-7 border-outline-gray-2 hover:bg-surface-gray-2',
        ]"
        @click="toggleQuickFilter(qf.value)"
      >
        {{ qf.label }}
        <span
          v-if="qf.count !== null && qf.count > 0"
          class="inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-bold min-w-[1.125rem]"
          :class="[
            activeQuickFilter === qf.value
              ? 'bg-white text-ink-gray-9'
              : qf.countClass,
          ]"
        >
          {{ qf.count }}
        </span>
      </button>
    </div>

    <!-- Task List -->
    <div class="flex-1 overflow-y-auto">
      <!-- Loading State -->
      <div
        v-if="tasksResource.loading && !tasksResource.data"
        class="flex items-center justify-center h-48"
      >
        <div class="flex items-center gap-2 text-ink-gray-5">
          <FeatherIcon name="loader" class="h-4 w-4 animate-spin" />
          <span class="text-sm">Aufgaben werden geladen...</span>
        </div>
      </div>

      <!-- Task Rows -->
      <div v-else-if="tasks.length" class="px-3 sm:px-5 py-1">
        <div
          v-for="(task, idx) in tasks"
          :key="task.name"
        >
          <div
            class="flex items-center gap-3 rounded-md px-3 py-3 cursor-pointer transition-colors hover:bg-surface-gray-1 group"
            @click="openEditModal(task)"
          >
            <!-- Left: Status Icon + Content -->
            <div class="flex items-start gap-3 flex-1 min-w-0">
              <!-- Status Quick-Change -->
              <Dropdown
                :options="taskStatusOptions(handleStatusChange, task)"
                @click.stop
              >
                <Tooltip :text="statusLabel(task.status)">
                  <button
                    class="mt-0.5 rounded p-0.5 transition-colors hover:bg-surface-gray-3"
                  >
                    <TaskStatusIcon :status="task.status" />
                  </button>
                </Tooltip>
              </Dropdown>

              <!-- Title + Description -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span
                    class="text-sm font-medium truncate"
                    :class="[
                      task.status === 'Done' || task.status === 'Canceled'
                        ? 'text-ink-gray-5 line-through'
                        : 'text-ink-gray-9',
                    ]"
                  >
                    {{ task.title }}
                  </span>
                </div>
                <div
                  v-if="task.description"
                  class="mt-0.5 text-xs text-ink-gray-5 truncate max-w-md"
                  v-html="stripHtml(task.description)"
                />
              </div>
            </div>

            <!-- Right: Meta Info -->
            <div class="flex items-center gap-3 shrink-0">
              <!-- Reference Link -->
              <Button
                v-if="task.reference_docname"
                variant="ghost"
                size="sm"
                class="text-xs"
                :label="referenceLabel(task)"
                @click.stop="navigateToReference(task)"
              >
                <template #suffix>
                  <FeatherIcon name="arrow-up-right" class="h-3 w-3" />
                </template>
              </Button>

              <!-- Priority Badge -->
              <Tooltip :text="priorityLabel(task.priority)">
                <span
                  class="inline-flex items-center gap-1 text-xs font-medium"
                  :class="priorityColor(task.priority)"
                >
                  <TaskPriorityIcon
                    :priority="task.priority"
                    class="!h-2 !w-2"
                  />
                  {{ priorityLabel(task.priority) }}
                </span>
              </Tooltip>

              <!-- Due Date -->
              <span
                class="inline-flex items-center gap-1 text-xs min-w-[5.5rem] justify-end"
                :class="dueDateClass(task)"
              >
                <FeatherIcon name="calendar" class="h-3 w-3" />
                <span>{{ dueDateText(task) }}</span>
              </span>

              <!-- Assigned User -->
              <Tooltip
                v-if="task.assigned_to"
                :text="task.assigned_to_name || task.assigned_to"
              >
                <Avatar
                  :label="task.assigned_to_name || task.assigned_to"
                  :image="task.assigned_to_image"
                  size="sm"
                />
              </Tooltip>
              <div v-else class="w-7" />
            </div>
          </div>

          <!-- Divider -->
          <div
            v-if="idx < tasks.length - 1"
            class="mx-3 border-t border-outline-gray-modals"
          />
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="tasksResource.data && !tasks.length"
        class="flex h-full items-center justify-center"
      >
        <div
          class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
        >
          <FeatherIcon name="check-circle" class="h-10 w-10" />
          <span>{{ emptyStateText }}</span>
          <Button
            label="Aufgabe erstellen"
            iconLeft="plus"
            @click="openCreateModal"
          />
        </div>
      </div>
    </div>

    <!-- Task Modal -->
    <TaskModal
      v-if="showTaskModal"
      v-model="showTaskModal"
      v-model:reloadTasks="tasksReloadProxy"
      :task="selectedTask"
    />
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import { taskStatusOptions } from '@/utils'
import { formatDate } from '@/utils'
import {
  Button,
  Avatar,
  Dropdown,
  Tooltip,
  FeatherIcon,
  createResource,
  usePageMeta,
  call,
} from 'frappe-ui'
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

usePageMeta(() => ({ title: __('Tasks') }))

const router = useRouter()

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const activeView = ref('open')
const activeQuickFilter = ref('')
const activeUser = ref('')
const showTaskModal = ref(false)

const selectedTask = ref({
  name: '',
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
  reference_doctype: 'CRM Lead',
  reference_docname: '',
})

// ---------------------------------------------------------------------------
// API Resources
// ---------------------------------------------------------------------------
const tasksResource = createResource({
  url: 'crm.api.tasks.get_tasks',
  makeParams() {
    return {
      view: activeView.value,
      quick_filter: activeQuickFilter.value,
      user_filter: activeUser.value,
    }
  },
  auto: true,
})

const taskUsers = createResource({
  url: 'crm.api.tasks.get_task_users',
  auto: true,
})

// Reload when filters change
watch([activeView, activeQuickFilter, activeUser], () => {
  tasksResource.reload()
})

// ---------------------------------------------------------------------------
// Computed data
// ---------------------------------------------------------------------------
const tasks = computed(() => tasksResource.data?.tasks || [])
const counts = computed(() => tasksResource.data?.counts || {
  open: 0,
  completed: 0,
  total: 0,
  overdue: 0,
})
const isManager = computed(() => tasksResource.data?.is_manager || false)

// Proxy object that exposes a reload() method for TaskModal's v-model:reloadTasks
const tasksReloadProxy = computed({
  get() {
    return { reload: () => tasksResource.reload() }
  },
  set() {
    // TaskModal may assign to this; trigger reload
    tasksResource.reload()
  },
})

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------
const allTabs = computed(() => [
  { value: 'open', label: 'Offen', count: counts.value.open },
  { value: 'completed', label: 'Abgeschlossen', count: counts.value.completed },
  { value: 'all', label: 'Alle', count: counts.value.total, managerOnly: true },
])

const visibleTabs = computed(() =>
  allTabs.value.filter((tab) => !tab.managerOnly || isManager.value),
)

// ---------------------------------------------------------------------------
// Quick Filters
// ---------------------------------------------------------------------------
const quickFilters = computed(() => [
  {
    value: 'overdue',
    label: 'Überfällig',
    count: counts.value.overdue,
    countClass: 'bg-red-100 text-red-600',
  },
  { value: 'today', label: 'Heute', count: null, countClass: '' },
  { value: 'this_week', label: 'Diese Woche', count: null, countClass: '' },
  { value: 'no_date', label: 'Ohne Datum', count: null, countClass: '' },
])

function toggleQuickFilter(value) {
  activeQuickFilter.value = activeQuickFilter.value === value ? '' : value
}

// ---------------------------------------------------------------------------
// User Filter (Manager only)
// ---------------------------------------------------------------------------
const userFilterOptions = computed(() => {
  const users = taskUsers.data || []
  const options = [
    {
      label: 'Alle',
      icon: 'users',
      onClick: () => {
        activeUser.value = ''
      },
    },
  ]
  users.forEach((u) => {
    options.push({
      label: u.full_name || u.email,
      image: u.user_image || null,
      onClick: () => {
        activeUser.value = u.email
      },
    })
  })
  return options
})

const activeUserLabel = computed(() => {
  if (!activeUser.value) return 'Alle'
  const u = (taskUsers.data || []).find((u) => u.email === activeUser.value)
  return u?.full_name || activeUser.value
})

const activeUserImage = computed(() => {
  if (!activeUser.value) return null
  const u = (taskUsers.data || []).find((u) => u.email === activeUser.value)
  return u?.user_image || null
})

// ---------------------------------------------------------------------------
// Status Labels (German)
// ---------------------------------------------------------------------------
const STATUS_LABELS = {
  Backlog: 'Backlog',
  Todo: 'Zu erledigen',
  'In Progress': 'In Bearbeitung',
  Done: 'Erledigt',
  Canceled: 'Abgebrochen',
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status
}

// ---------------------------------------------------------------------------
// Priority Labels (German) and Colors
// ---------------------------------------------------------------------------
const PRIORITY_LABELS = {
  High: 'Hoch',
  Medium: 'Mittel',
  Low: 'Niedrig',
}

function priorityLabel(priority) {
  return PRIORITY_LABELS[priority] || priority
}

function priorityColor(priority) {
  const map = {
    High: 'text-red-500',
    Medium: 'text-orange-500',
    Low: 'text-gray-400',
  }
  return map[priority] || 'text-gray-400'
}

// ---------------------------------------------------------------------------
// Due Date Display
// ---------------------------------------------------------------------------
function dueDateClass(task) {
  if (task.is_overdue) return 'text-red-600 font-medium'
  if (task.is_today) return 'text-orange-600 font-medium'
  if (task.due_date) return 'text-ink-gray-5'
  return 'text-ink-gray-4 italic'
}

function dueDateText(task) {
  if (!task.due_date) return 'Kein Datum'
  if (task.is_overdue) return 'Überfällig'
  if (task.is_today) return 'Heute'
  return formatDate(task.due_date, '', true)
}

// ---------------------------------------------------------------------------
// Reference Link
// ---------------------------------------------------------------------------
function referenceLabel(task) {
  if (task.reference_doctype === 'CRM Deal') return 'Deal'
  return 'Lead'
}

function navigateToReference(task) {
  if (!task.reference_docname) return
  if (task.reference_doctype === 'CRM Deal') {
    router.push({ name: 'Deal', params: { dealId: task.reference_docname } })
  } else {
    router.push({ name: 'Lead', params: { leadId: task.reference_docname } })
  }
}

// ---------------------------------------------------------------------------
// Status Quick-Change
// ---------------------------------------------------------------------------
async function handleStatusChange(status, task) {
  if (!task?.name) return
  await call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: { status },
  })
  tasksResource.reload()
}

// ---------------------------------------------------------------------------
// Task Modal
// ---------------------------------------------------------------------------
function openCreateModal() {
  selectedTask.value = {
    name: '',
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    status: 'Backlog',
    priority: 'Low',
    reference_doctype: 'CRM Lead',
    reference_docname: '',
  }
  showTaskModal.value = true
}

function openEditModal(task) {
  selectedTask.value = {
    name: task.name,
    title: task.title,
    description: task.description || '',
    assigned_to: task.assigned_to || '',
    due_date: task.due_date || '',
    status: task.status,
    priority: task.priority,
    reference_doctype: task.reference_doctype || '',
    reference_docname: task.reference_docname || '',
  }
  showTaskModal.value = true
}

// ---------------------------------------------------------------------------
// Empty State Text
// ---------------------------------------------------------------------------
const emptyStateText = computed(() => {
  if (activeQuickFilter.value === 'overdue') return 'Keine überfälligen Aufgaben'
  if (activeQuickFilter.value === 'today') return 'Keine Aufgaben für heute'
  if (activeQuickFilter.value === 'this_week') return 'Keine Aufgaben diese Woche'
  if (activeQuickFilter.value === 'no_date') return 'Keine Aufgaben ohne Datum'
  if (activeView.value === 'completed') return 'Keine abgeschlossenen Aufgaben'
  return 'Keine Aufgaben gefunden'
})

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}
</script>
