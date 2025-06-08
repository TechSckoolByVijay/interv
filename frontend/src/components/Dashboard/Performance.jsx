// Example for Performance.jsx
// filepath: c:\Learning Lab\GenAI\interviewer\frontend\src\components\Dashboard\Performance.jsx
import React from "react";
import { Paper, Typography, Box } from "@mui/material";
export default function Performance() {
  return (
    <Box sx={{ maxWidth: 900, mx: "auto", mt: 4 }}>
      <Paper elevation={8} sx={{ p: 4, borderRadius: 4 }}>
        <Typography variant="h4" color="primary" fontWeight={800} mb={2}>
          Interview Performance
        </Typography>
        <Typography color="text.secondary">
          Your completed interviews and feedback will appear here.
        </Typography>
      </Paper>
    </Box>
  );
}