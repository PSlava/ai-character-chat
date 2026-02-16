import axios from 'axios';
import { getToken, getAnonSessionId } from '@/lib/supabase';

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

export default api;
