import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TextField, Button, Paper, Typography, Box, MenuItem } from "@mui/material";
import axios from "../../api";

export default function SignupForm() {
  const [form, setForm] = useState({ username: "", password: "", user_type: "CANDIDATE" });
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/signup", form);
      alert("Signup successful! Please login.");
      navigate("/login");
    } catch (err) {
      alert("Signup failed");
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
      <Paper elevation={3} sx={{ p: 4, width: 350 }}>
        <Typography variant="h5" mb={2}>Sign Up</Typography>
        <form onSubmit={handleSubmit}>
          <TextField label="Username" name="username" fullWidth margin="normal" onChange={handleChange} required />
          <TextField label="Password" name="password" type="password" fullWidth margin="normal" onChange={handleChange} required />
          <TextField
            select
            label="User Type"
            name="user_type"
            value={form.user_type}
            onChange={handleChange}
            fullWidth
            margin="normal"
            required
          >
            <MenuItem value="ADMIN">Admin</MenuItem>
            <MenuItem value="CANDIDATE">Candidate</MenuItem>
          </TextField>
          <Button type="submit" variant="contained" color="primary" fullWidth>Sign Up</Button>
        </form>
        <Button onClick={() => navigate("/login")} fullWidth sx={{ mt: 2 }}>Back to Login</Button>
      </Paper>
    </Box>
  );
}