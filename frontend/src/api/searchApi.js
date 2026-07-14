import axiosClient from './axiosClient';

export const searchApi = {
  semanticSearch: async (projectId, query) => {
    const response = await axiosClient.post('/search', {
      project_id: projectId,
      query: query
    });
    return response.data;
  }
};
