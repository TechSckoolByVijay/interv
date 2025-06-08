import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Box, useTheme } from "@mui/material";
import LoginForm from "./components/Auth/LoginForm";
import SignupForm from "./components/Auth/SignupForm";
import ProtectedRoute from "./components/Common/ProtectedRoute";
import Interview from "./components/Dashboard/Interview";
import JDResume from "./components/Dashboard/JDResume";
import Performance from "./components/Dashboard/Performance";
import Support from "./components/Dashboard/Support";
import Sidebar from "./components/Dashboard/Sidebar";

const drawerWidth = 10;

function App() {
  const theme = useTheme();
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/signup" element={<SignupForm />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <div style={{ display: "flex" }}>
                <Sidebar />
                <Box
                  component="main"
                  sx={{
                    flex: 1,
                    marginLeft: `${drawerWidth}px`,
                    padding: "32px 24px",
                    background: theme.palette.background.default,
                    minHeight: "100vh",
                  }}
                >
                  <Routes>
                    <Route path="interview" element={<Interview />} />
                    <Route path="jd-resume" element={<JDResume />} />
                    <Route path="performance" element={<Performance />} />
                    <Route path="support" element={<Support />} />
                    <Route path="*" element={<Navigate to="/interview" />} />
                  </Routes>
                </Box>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;