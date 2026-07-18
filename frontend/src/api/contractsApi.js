import axiosClient from './axiosClient';

export const contractsApi = {
  getContracts: async (projectId) => {
    // Optionally pass projectId as query param to filter
    const url = projectId ? `/contracts?project_id=${projectId}` : '/contracts';
    const response = await axiosClient.get(url);
    return response.data;
  },

  getContract: async (contractId) => {
    const response = await axiosClient.get(`/contracts/${contractId}`);
    return response.data;
  },

  uploadContract: async (projectId, file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axiosClient.post(`/contracts?project_id=${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteContract: async (contractId) => {
    await axiosClient.delete(`/contracts/${contractId}`);
  },

  downloadContract: async (contractId, filename) => {
    const response = await axiosClient.get(`/contracts/${contractId}/download`, {
      responseType: 'blob', // Important for handling binary data
    });
    
    // Create a blob and trigger download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || 'downloaded_contract');
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
};
