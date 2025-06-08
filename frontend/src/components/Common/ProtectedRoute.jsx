import React from "react";
import { Navigate } from "react-router-dom";

// Dummy authentication check (replace with real logic)
const isAuthenticated = () => {
  // For now, always allow. Replace with token/session check.
  return true;
};

export default function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  return children;
}