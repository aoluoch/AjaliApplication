import axios from 'axios';

const API_URL = 'https://ajaliapplication-isto.onrender.com/';

const getReviews = async (incidentId) => {
  const response = await axios.get(`${API_URL}/incidents/${incidentId}/reviews`, {
    withCredentials: true
  });
  return response.data;
};

const createReview = async (incidentId, reviewData) => {
  const response = await axios.post(
    `${API_URL}/incidents/${incidentId}/reviews`,
    reviewData,
    { withCredentials: true }
  );
  return response.data;
};

const deleteReview = async (incidentId, reviewId) => {
  await axios.delete(`${API_URL}/incidents/${incidentId}/reviews/${reviewId}`, {
    withCredentials: true
  });
};

export { getReviews, createReview, deleteReview };