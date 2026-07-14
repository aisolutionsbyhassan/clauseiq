import axiosClient from './axiosClient';

export const analysisApi = {
  getClauses: async (contractId) => {
    const response = await axiosClient.get(`/contracts/${contractId}/clauses`);
    return response.data;
  },

  extractClauses: async (contractId) => {
    const response = await axiosClient.post(`/contracts/${contractId}/clauses`);
    return response.data;
  },

  getRisks: async (contractId) => {
    const response = await axiosClient.get(`/contracts/${contractId}/risks`);
    return response.data;
  },

  detectRisks: async (contractId) => {
    const response = await axiosClient.post(`/contracts/${contractId}/risks`);
    return response.data;
  },

  getSummary: async (contractId) => {
    const response = await axiosClient.get(`/contracts/${contractId}/summary`);
    return response.data;
  },

  generateSummary: async (contractId) => {
    const response = await axiosClient.post(`/contracts/${contractId}/summary`);
    return response.data;
  }
};
