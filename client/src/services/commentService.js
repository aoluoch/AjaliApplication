import axios from 'axios';

const API_URL = 'https://ajaliapplication-isto.onrender.com';

export const getComments = async (incidentId) => {
  const response = await axios.get(`${API_URL}/incidents/${incidentId}/comments`, {
    withCredentials: true
  });
  return response.data;
};

export const createComment = async (incidentId, content) => {
  const response = await axios.post(
    `${API_URL}/incidents/${incidentId}/comments`,
    { content },
    { withCredentials: true }
  );
  return response.data;
};

export const deleteComment = async (incidentId, commentId) => {
  await axios.delete(`${API_URL}/incidents/${incidentId}/comments/${commentId}`, {
    withCredentials: true
  });
};