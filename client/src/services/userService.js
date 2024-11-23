import axios from 'axios';

const API_URL = 'https://ajaliapplication-isto.onrender.com';

export const getAllUsers = async () => {
  const response = await axios.get(`${API_URL}/users`, {
    withCredentials: true
  });
  return response.data;
};

export const deleteUser = async (id) => {
  await axios.delete(`${API_URL}/users/${id}`, {
    withCredentials: true
  });
};

export const banUser = async (id, isBanned) => {
  const response = await axios.put(
    `${API_URL}/users/${id}/ban`,
    { is_banned: isBanned },
    { withCredentials: true }
  );
  return response.data;
};