import axios from 'axios';
import { getToken, getAnonSessionId, removeToken, removeUser } from '@/lib/supabase';

const api = axios.create({
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    config.headers['X-Anon-Session'] = getAnonSessionId();
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && getToken()) {
      // Token expired or invalid — clear auth and redirect to home
      removeToken();
      removeUser();
      window.location.href = '/';
    }
    return Promise.reject(error);
  },
);

export default api;
