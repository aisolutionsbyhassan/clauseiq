import axiosClient from './axiosClient';

export const chatApi = {
  getHistory: async (contractId) => {
    const response = await axiosClient.get(`/contracts/${contractId}/chat`);
    return response.data;
  },

  sendMessage: async (contractId, question) => {
    const response = await axiosClient.post(`/contracts/${contractId}/chat`, { question });
    return response.data;
  },

  clearHistory: async (contractId) => {
    await axiosClient.delete(`/contracts/${contractId}/chat`);
  }
};
