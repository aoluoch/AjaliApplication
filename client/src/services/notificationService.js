import axios from './axiosConfig';

export const getNotifications = async () => {
  const response = await axios.get('https://ajaliapplication-isto.onrender.com/notifications');
  return response.data;
};

export const markNotificationAsRead = async (id) => {
  const response = await axios.put(`https://ajaliapplication-isto.onrender.com/notifications/${id}`);
  return response.data;
};