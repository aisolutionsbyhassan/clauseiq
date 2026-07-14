import axiosClient from './axiosClient';

export const projectsApi = {
  getProjects: async () => {
    const response = await axiosClient.get('/projects');
    return response.data;
  },
  
  getProject: async (projectId) => {
    const response = await axiosClient.get(`/projects/${projectId}`);
    return response.data;
  },

  createProject: async (name, description) => {
    const response = await axiosClient.post('/projects', { name, description });
    return response.data;
  },

  updateProject: async (projectId, data) => {
    const response = await axiosClient.patch(`/projects/${projectId}`, data);
    return response.data;
  },

  deleteProject: async (projectId) => {
    await axiosClient.delete(`/projects/${projectId}`);
  }
};
