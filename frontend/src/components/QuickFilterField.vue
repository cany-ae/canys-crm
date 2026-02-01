<template>
  <FormControl
    v-if="filter.fieldtype == 'Check'"
    :label="filter.label"
    type="checkbox"
    v-model="filter.value"
    @change.stop="updateFilter(filter, $event.target.checked)"
  />
  <FormControl
    v-else-if="filter.fieldtype === 'Select'"
    class="form-control cursor-pointer [&_select]:cursor-pointer"
    type="select"
    v-model="filter.value"
    :options="filter.options"
    :placeholder="filter.label"
    @change.stop="updateFilter(filter, $event.target.value)"
  />
  <Link
    v-else-if="filter.fieldtype === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    @change="(data) => updateFilter(filter, data)"
  />
  <component
    v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
    class="border-none"
    :is="filter.fieldtype === 'Date' ? DatePicker : DateTimePicker"
    :value="filter.value"
    @change="(v) => updateFilter(filter, v)"
    :placeholder="filter.label"
  />
  <div v-else class="relative">
    <div
      v-if="filter.fieldname === 'lead_name'"
      class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-2.5"
    >
      <svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
    <FormControl
      v-model="filter.value"
      type="text"
      :placeholder="filter.fieldname === 'lead_name' ? 'Suche' : filter.label"
      :class="filter.fieldname === 'lead_name' ? '[&_input]:pl-8' : ''"
      @input.stop="debouncedFn(filter, $event.target.value)"
    />
  </div>
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl, DatePicker, DateTimePicker } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['applyQuickFilter'])

const debouncedFn = useDebounceFn((f, value) => {
  emit('applyQuickFilter', f, value)
}, 500)

function updateFilter(f, value) {
  emit('applyQuickFilter', f, value)
}
</script>
