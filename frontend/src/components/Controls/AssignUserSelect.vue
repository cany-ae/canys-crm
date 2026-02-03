<template>
  <div class="space-y-1.5 p-[2px] -m-[2px]">
    <label class="block text-xs text-ink-gray-5" v-if="label">
      {{ __(label) }}
    </label>
    <Autocomplete
      ref="autocomplete"
      :options="filteredOptions"
      v-model="selectedValue"
      :size="size || 'sm'"
      :variant="variant"
      :placeholder="placeholder"
      :disabled="disabled"
    >
      <template #target="{ open, togglePopover }">
        <slot name="target" v-bind="{ open, togglePopover }" />
      </template>
      <template #prefix>
        <slot name="prefix" />
      </template>
      <template #item-prefix="{ active, selected, option }">
        <slot name="item-prefix" v-bind="{ active, selected, option }" />
      </template>
      <template #item-label="{ active, selected, option }">
        <slot name="item-label" v-bind="{ active, selected, option }">
          <div class="flex-1 truncate text-ink-gray-7">
            {{ option.label }}
          </div>
        </slot>
      </template>
      <template #footer="{ close }">
        <div>
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Clear')"
            iconLeft="x"
            @click="() => clearValue(close)"
          />
        </div>
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { usersStore } from '@/stores/users'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  value: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  label: { type: String, default: '' },
  size: { type: String, default: 'sm' },
  variant: { type: String, default: undefined },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const { assignableUsers, getUser } = usersStore()
const autocomplete = ref(null)

const valuePropPassed = computed(() => 'value' in props && props.value !== '')

const selectedValue = computed({
  get: () => (valuePropPassed.value ? props.value : props.modelValue),
  set: (val) => {
    const v = val?.value || ''
    emit(valuePropPassed.value ? 'change' : 'update:modelValue', v)
  },
})

const filteredOptions = computed(() => {
  const query = (autocomplete.value?.query || '').toLowerCase()
  const users = assignableUsers.value || []

  // Fail-closed: if no data loaded, return empty (UI shows nothing, not everything)
  if (!users.length) return []

  return users
    .filter((u) => {
      if (!query) return true
      return (
        (u.full_name || '').toLowerCase().includes(query) ||
        (u.name || '').toLowerCase().includes(query)
      )
    })
    .map((u) => ({
      label: u.full_name || u.name,
      value: u.name,
    }))
})

function clearValue(close) {
  emit(valuePropPassed.value ? 'change' : 'update:modelValue', '')
  close()
}
</script>
