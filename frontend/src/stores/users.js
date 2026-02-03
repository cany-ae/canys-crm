import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { sessionStore } from './session'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

export const usersStore = defineStore('crm-users', () => {
  const session = sessionStore()

  let usersByName = reactive({})
  const router = useRouter()

  const assignableUsers = ref([])

  const users = createResource({
    url: 'crm.api.session.get_users',
    cache: 'crm-users',
    initialData: [],
    auto: true,
    transform([allUsers, crmUsers]) {
      for (let user of allUsers) {
        usersByName[user.name] = user
        if (user.name === 'Administrator') {
          usersByName[user.email] = user
        }
      }
      return { allUsers, crmUsers }
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })

  let _assignRetries = 0
  console.log('[UsersStore] creating assignableUsersResource, auto=true')
  const assignableUsersResource = createResource({
    url: 'crm.api.session.get_assignable_users',
    initialData: [],
    auto: true,
    onSuccess(data) {
      _assignRetries = 0
      assignableUsers.value = data || []
      console.log('[AssignableUsers] loaded', assignableUsers.value.length, 'users')
    },
    onError(error) {
      console.error('[AssignableUsers] API error, retry', _assignRetries, error)
      if (_assignRetries < 3) {
        _assignRetries++
        setTimeout(() => assignableUsersResource.reload(), 2000 * _assignRetries)
      }
    },
  })

  function getAssignableUserNames() {
    const names = assignableUsers.value.map((u) => u.name)
    // Fallback: if not loaded yet, only allow self-assignment
    if (!names.length) return [session.user]
    return names
  }

  function reloadAssignableUsers() {
    assignableUsersResource.reload()
  }

  function getUser(email) {
    if (!email || email === 'sessionUser') {
      email = session.user
    }
    if (!usersByName[email]) {
      usersByName[email] = {
        name: email,
        email: email,
        full_name: email.split('@')[0],
        first_name: email.split('@')[0],
        last_name: '',
        user_image: null,
        role: null,
      }
    }
    return usersByName[email]
  }

  function isAdmin(email) {
    return getUser(email).role === 'System Manager'
  }

  function isManager(email) {
    return getUser(email).role === 'Sales Manager' || isAdmin(email)
  }

  function isWebsiteUser(email) {
    return getUser(email).user_type === 'Website User'
  }

  function isSalesUser(email) {
    return getUser(email).role === 'Sales User'
  }

  function isTelephonyAgent(email) {
    return getUser(email).is_telphony_agent
  }

  function getUserRole(email) {
    const user = getUser(email)
    if (user && user.role) {
      return user.role
    }
    return null
  }

  return {
    users,
    assignableUsers,
    getAssignableUserNames,
    reloadAssignableUsers,
    getUser,
    isAdmin,
    isManager,
    isSalesUser,
    isTelephonyAgent,
    getUserRole,
    isWebsiteUser,
  }
})
