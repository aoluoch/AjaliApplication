import axios from 'axios';

const instance = axios.create({
  baseURL: 'https://ajaliapplication-isto.onrender.com/',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
});

instance.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

export default instance;