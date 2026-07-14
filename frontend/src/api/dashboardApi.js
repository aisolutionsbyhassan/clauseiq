import axiosClient from './axiosClient';

export const dashboardApi = {
  getDashboard: async () => {
    const response = await axiosClient.get('/dashboard');
    return response.data;
  },
};
