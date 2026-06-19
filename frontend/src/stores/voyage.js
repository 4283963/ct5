import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getVoyageList } from '@/api/metrics'

export const useVoyageStore = defineStore('voyage', () => {
  const voyages = ref([])
  const selectedVoyages = ref([])
  const loading = ref(false)
  const total = ref(0)

  const voyageOptions = computed(() => {
    return voyages.value.map(v => ({
      label: `${v.vessel_name} - ${v.departure_port} → ${v.arrival_port}`,
      value: v.voyage_id,
      ...v
    }))
  })

  const selectedVoyageDetails = computed(() => {
    return selectedVoyages.value.map(id =>
      voyages.value.find(v => v.voyage_id === id)
    ).filter(Boolean)
  })

  async function fetchVoyages(params = {}) {
    loading.value = true
    try {
      const response = await getVoyageList(params)
      voyages.value = response.voyages
      total.value = response.total
      return response
    } finally {
      loading.value = false
    }
  }

  function selectVoyage(voyageId) {
    if (!selectedVoyages.value.includes(voyageId)) {
      selectedVoyages.value.push(voyageId)
    }
  }

  function deselectVoyage(voyageId) {
    const index = selectedVoyages.value.indexOf(voyageId)
    if (index > -1) {
      selectedVoyages.value.splice(index, 1)
    }
  }

  function toggleVoyageSelection(voyageId) {
    if (selectedVoyages.value.includes(voyageId)) {
      deselectVoyage(voyageId)
    } else {
      selectVoyage(voyageId)
    }
  }

  function clearSelection() {
    selectedVoyages.value = []
  }

  return {
    voyages,
    selectedVoyages,
    loading,
    total,
    voyageOptions,
    selectedVoyageDetails,
    fetchVoyages,
    selectVoyage,
    deselectVoyage,
    toggleVoyageSelection,
    clearSelection
  }
})
