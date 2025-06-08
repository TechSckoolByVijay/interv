import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TextField, Button, Paper, Typography, Box } from "@mui/material";
import axios from "../../api";

export default function LoginForm() {
  const [form, setForm] = useState({ username: "", password: "" });
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("/login", form);
      // After successful login
      localStorage.setItem("user_data", JSON.stringify(response.data.user_data));
      navigate("/interview");
    } catch (error) {
      console.error("Login failed:", error);
      // Handle login error (e.g., show notification)
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      sx={{
        background: "linear-gradient(135deg, #232b3b 60%, #2979ff 100%)"
      }}
    >
      <Paper elevation={6} sx={{ p: 4, width: 350, borderRadius: 4, boxShadow: "0 8px 32px 0 rgba(41,121,255,0.18)" }}>
        <Box textAlign="center" mb={2}>
          <img src="/logo192.png" alt="Logo" style={{ width: 40, marginBottom: 8 }} />
          <Typography variant="h5" fontWeight={700}>Login</Typography>
        </Box>
        <form onSubmit={handleSubmit}>
          <TextField label="Username" name="username" fullWidth margin="normal" onChange={handleChange} />
          <TextField label="Password" name="password" type="password" fullWidth margin="normal" onChange={handleChange} />
          <Button type="submit" variant="contained" color="primary" fullWidth>Login</Button>
        </form>
        <Button onClick={() => navigate("/signup")} fullWidth sx={{ mt: 2 }}>Sign Up</Button>
      </Paper>
    </Box>
  );
}