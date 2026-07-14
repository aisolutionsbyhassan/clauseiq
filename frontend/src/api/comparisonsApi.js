import axiosClient from './axiosClient';

export const comparisonsApi = {
  listComparisons: async (projectId) => {
    const response = await axiosClient.get(`/comparisons?project_id=${projectId}`);
    return response.data;
  },

  getComparison: async (comparisonId) => {
    const response = await axiosClient.get(`/comparisons/${comparisonId}`);
    return response.data;
  },

  createComparison: async (projectId, contractAId, contractBId) => {
    const response = await axiosClient.post(`/comparisons?project_id=${projectId}`, {
      contract_a_id: contractAId,
      contract_b_id: contractBId
    });
    return response.data;
  }
};
