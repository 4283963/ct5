import api from './index'

export const getVoyageList = (params = {}) => {
  return api.get('/metrics/voyages', { params })
}

export const getVoyageSummary = (voyageId) => {
  return api.get(`/metrics/voyages/${voyageId}`)
}

export const getVoyageMetrics = (voyageId) => {
  return api.get(`/metrics/voyages/${voyageId}/metrics`)
}

export const getVoyageTrajectory = (voyageId) => {
  return api.get(`/metrics/voyages/${voyageId}/trajectory`)
}

export const compareVoyages = (data) => {
  return api.post('/metrics/comparison', data)
}

export const getSpeedFuelCorrelation = (voyageId) => {
  return api.get(`/metrics/voyages/${voyageId}/speed-fuel-correlation`)
}

export const getWindImpact = (voyageId) => {
  return api.get(`/metrics/voyages/${voyageId}/wind-impact`)
}

export const getOptimalSpeed = (voyageId) => {
  return api.get(`/metrics/voyages/${voyageId}/optimal-speed`)
}

export const getRollingEfficiency = (voyageId, window = 10) => {
  return api.get(`/metrics/voyages/${voyageId}/rolling-efficiency`, {
    params: { window }
  })
}

export const getFuelTypes = () => {
  return api.get('/metrics/carbon/fuel-types')
}

export const predictCarbonEmission = (data) => {
  return api.post('/metrics/carbon/predict', data)
}
