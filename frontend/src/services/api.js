import axios from 'axios';

const API = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000' });

// Users
export const getUsers  = (skip=0,limit=100) => API.get(`/users/?skip=${skip}&limit=${limit}`);
export const getUser   = (id)               => API.get(`/users/${id}`);

// Transactions
export const getTransactions = (params={}) => API.get('/transactions/', { params });

// Budgets
export const getBudgets = (user_id) => API.get('/budgets/', { params: { user_id } });

// Insights
export const getInsights = (user_id) => API.get('/insights/', { params: { user_id } });

// Merchants
export const getMerchants = () => API.get('/merchants/');

// Categories
export const getCategories = () => API.get('/categories/');

// Recurring Series
export const getRecurringSeries = (account_id) =>
  API.get('/recurring-series/', { params: { account_id } });

// Analytics
export const getSpendingByCategory = (user_id, year, month) =>
  API.get('/analytics/spending-by-category', { params: { user_id, year, month } });

export const getMonthlyTrend = (user_id, year) =>
  API.get('/analytics/monthly-trend', { params: { user_id, year } });

export const getBudgetComparison = (user_id, year, month) =>
  API.get('/analytics/budget-comparison', { params: { user_id, year, month } });

// Data generation
export const generateData = (users=100, transactions_per_user=500, seed=20261022) =>
  API.post('/generate-data', null, { params: { users, transactions_per_user, seed } });
