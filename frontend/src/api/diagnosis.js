import api from './index'

export const diagnoseVoyage = (data) => {
  return api.post('/diagnosis/voyage', data)
}

export const getVoyageDiagnosis = (voyageId, includeSuggestions = true) => {
  return api.get(`/diagnosis/voyage/${voyageId}`, {
    params: { include_suggestions: includeSuggestions }
  })
}

export const batchDiagnose = (data) => {
  return api.post('/diagnosis/batch', data)
}

export const getOptimizationPlan = (voyageId) => {
  return api.get(`/diagnosis/voyage/${voyageId}/optimization-plan`)
}

export const getVoyageIssues = (voyageId, severity = null) => {
  return api.get(`/diagnosis/voyage/${voyageId}/issues`, {
    params: { severity }
  })
}

export const getEfficiencyRanking = (limit = 10) => {
  return api.get('/diagnosis/ranking', {
    params: { limit }
  })
}

export const getDiagnosisStatistics = () => {
  return api.get('/diagnosis/statistics')
}
