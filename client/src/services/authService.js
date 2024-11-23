import axios from './axiosConfig';

export const login = async (email, password) => {
  const response = await axios.post('https://ajaliapplication-isto.onrender.com/login', { email, password });
  return response.data;
};

export const register = async (userData) => {
  const response = await axios.post('https://ajaliapplication-isto.onrender.com/register', userData);
  return response.data;
};

export const logout = async () => {
  const response = await axios.post('https://ajaliapplication-isto.onrender.com/logout');
  return response.data;
};

export const checkSession = async () => {
  const response = await axios.get('https://ajaliapplication-isto.onrender.com/check_session');
  return response.data;
};