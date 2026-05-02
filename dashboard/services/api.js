import axios from "axios";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/reports/api",
});

export const getDailyProduction = () => API.get("/production/daily/");
export const getMonthlySummary = () => API.get("/production/monthly/");
export const getTopParties = () => API.get("/production/top-parties/");