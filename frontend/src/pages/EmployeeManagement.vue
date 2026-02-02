<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: 'Mitarbeiterverwaltung', route: { name: 'Employee Management' } }]" />
    </template>
    <template #right-header>
      <Button variant="solid" @click="showCreateDialog = true">
        <template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
        Neuer Mitarbeiter
      </Button>
    </template>
  </LayoutHeader>

  <div class="p-6">
    <!-- Error/Success Messages -->
    <div v-if="statusMessage" :class="[
      'mb-4 p-3 rounded-lg text-sm',
      statusMessage.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
    ]">
      {{ statusMessage.text }}
    </div>

    <!-- Employee List -->
    <div class="bg-white rounded-lg border">
      <div class="px-4 py-3 border-b">
        <h3 class="text-lg font-medium text-gray-900">Mitarbeiter</h3>
      </div>

      <div v-if="loading" class="p-8 text-center text-gray-500">
        Laden...
      </div>

      <div v-else-if="employees.length === 0" class="p-8 text-center text-gray-500">
        Noch keine Mitarbeiter angelegt.
      </div>

      <table v-else class="w-full">
        <thead>
          <tr class="border-b bg-gray-50">
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">E-Mail</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Profil</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Erstellt</th>
            <th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="emp in employees" :key="emp.name" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 text-sm font-medium text-gray-900">
              {{ emp.first_name }} {{ emp.last_name }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ emp.email || emp.name }}</td>
            <td class="px-4 py-3 text-sm">
              <span :class="profileBadgeClass(emp.role_profile_name)">
                {{ emp.role_profile_name || 'Kein Profil' }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span :class="emp.enabled ? 'text-green-600' : 'text-red-600'">
                {{ emp.enabled ? 'Aktiv' : 'Deaktiviert' }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500">{{ formatDate(emp.creation) }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-2">
                <Button
                  size="sm"
                  :variant="emp.enabled ? 'subtle' : 'solid'"
                  @click="toggleEmployee(emp)"
                >
                  {{ emp.enabled ? 'Deaktivieren' : 'Aktivieren' }}
                </Button>
                <Button size="sm" variant="subtle" @click="resetPassword(emp)">
                  Passwort-Reset
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Create Employee Dialog -->
  <Dialog v-model="showCreateDialog" :options="{ title: 'Neuen Mitarbeiter anlegen', size: 'md' }">
    <template #body-content>
      <div class="space-y-4">
        <FormControl
          label="Vorname"
          v-model="newEmployee.first_name"
          type="text"
          placeholder="Max"
          required
        />
        <FormControl
          label="Nachname"
          v-model="newEmployee.last_name"
          type="text"
          placeholder="Mustermann"
          required
        />
        <FormControl
          label="E-Mail"
          v-model="newEmployee.email"
          type="email"
          placeholder="max@example.de"
          required
        />
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Profil</label>
          <select
            v-model="newEmployee.profile"
            class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="" disabled>Profil auswählen...</option>
            <option value="Vertriebler">Vertriebler (CRM + Learning)</option>
            <option value="Geschäftsführer">Geschäftsführer (CRM + Learning + Insights)</option>
          </select>
        </div>

        <div v-if="createError" class="p-3 rounded bg-red-50 text-red-700 text-sm">
          {{ createError }}
        </div>
      </div>
    </template>
    <template #actions>
      <Button variant="solid" :loading="creating" @click="createEmployee" class="w-full">
        Mitarbeiter anlegen
      </Button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Button, Dialog, FormControl, FeatherIcon } from 'frappe-ui'

const employees = ref([])
const loading = ref(true)
const showCreateDialog = ref(false)
const creating = ref(false)
const createError = ref('')
const statusMessage = ref(null)

const newEmployee = ref({
  first_name: '',
  last_name: '',
  email: '',
  profile: '',
})

function profileBadgeClass(profile) {
  const base = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium'
  if (profile === 'Geschäftsführer') return `${base} bg-purple-100 text-purple-800`
  if (profile === 'Vertriebler') return `${base} bg-blue-100 text-blue-800`
  if (profile === 'Sales') return `${base} bg-gray-100 text-gray-800`
  return `${base} bg-gray-100 text-gray-500`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

async function loadEmployees() {
  loading.value = true
  try {
    const res = await call('crm.api.employee_management.get_employees')
    employees.value = res || []
  } catch (e) {
    console.error('Error loading employees:', e)
    statusMessage.value = { type: 'error', text: 'Fehler beim Laden der Mitarbeiter.' }
  } finally {
    loading.value = false
  }
}

async function createEmployee() {
  createError.value = ''
  const { first_name, last_name, email, profile } = newEmployee.value
  if (!first_name || !last_name || !email || !profile) {
    createError.value = 'Bitte alle Felder ausfüllen.'
    return
  }

  creating.value = true
  try {
    const res = await call('crm.api.employee_management.create_employee', {
      first_name, last_name, email, profile
    })
    statusMessage.value = { type: 'success', text: res.message }
    showCreateDialog.value = false
    newEmployee.value = { first_name: '', last_name: '', email: '', profile: '' }
    await loadEmployees()
  } catch (e) {
    createError.value = e.messages?.[0] || e.message || 'Fehler beim Erstellen.'
  } finally {
    creating.value = false
  }
}

async function toggleEmployee(emp) {
  try {
    const res = await call('crm.api.employee_management.toggle_employee', {
      email: emp.name,
      enabled: emp.enabled ? 0 : 1,
    })
    statusMessage.value = { type: 'success', text: res.message }
    await loadEmployees()
  } catch (e) {
    statusMessage.value = { type: 'error', text: e.messages?.[0] || 'Fehler.' }
  }
}

async function resetPassword(emp) {
  try {
    const res = await call('crm.api.employee_management.reset_employee_password', {
      email: emp.name,
    })
    statusMessage.value = { type: 'success', text: res.message }
  } catch (e) {
    statusMessage.value = { type: 'error', text: e.messages?.[0] || 'Fehler.' }
  }
}

onMounted(loadEmployees)
</script>
