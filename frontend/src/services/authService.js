
import API from "./api";

// Register a new user
export const registerUser = async (userData) => {
  const response = await API.post("/auth/register", userData);
  return response.data;
};

// Login existing user
export const loginUser = async (credentials) => {
  const response = await API.post("/auth/login", credentials);

  // Save JWT token
  localStorage.setItem("access_token", response.data.access_token);

  return response.data;
};

// Logout user
export const logoutUser = () => {
  localStorage.removeItem("access_token");
};
