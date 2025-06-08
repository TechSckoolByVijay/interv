import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  IconButton,
  CircularProgress,
  Stack,
  Avatar,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import DeleteIcon from "@mui/icons-material/Delete";
import VisibilityIcon from "@mui/icons-material/Visibility";
import DescriptionIcon from "@mui/icons-material/Description";
import AssignmentIndIcon from "@mui/icons-material/AssignmentInd";
import axios from "../../api";

const FILE_TYPES = [
  { key: "jd", label: "Job Description", icon: <DescriptionIcon fontSize="large" color="primary" /> },
  { key: "resume", label: "Resume", icon: <AssignmentIndIcon fontSize="large" color="secondary" /> },
];

const USER_ID = JSON.parse(localStorage.getItem("user_data"))?.id;

export default function JDResume() {
  const [files, setFiles] = useState({ jd: null, resume: null });
  const [loading, setLoading] = useState({ jd: false, resume: false });

  useEffect(() => {
    FILE_TYPES.forEach(async ({ key }) => {
      try {
        setLoading((prev) => ({ ...prev, [key]: true }));
        await axios.get(`/api/files/preview/${USER_ID}/${key}`, { responseType: "blob" });
        setFiles((prev) => ({ ...prev, [key]: true }));
      } catch {
        setFiles((prev) => ({ ...prev, [key]: null }));
      } finally {
        setLoading((prev) => ({ ...prev, [key]: false }));
      }
    });
  }, []);

  const handleUpload = async (e, fileType) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading((prev) => ({ ...prev, [fileType]: true }));
    const formData = new FormData();
    formData.append("file", file);
    try {
      await axios.post(`/api/files/upload/${USER_ID}/${fileType}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setFiles((prev) => ({ ...prev, [fileType]: true }));
      alert(`${fileType === "jd" ? "JD" : "Resume"} uploaded successfully!`);
    } catch {
      alert("Upload failed");
    } finally {
      setLoading((prev) => ({ ...prev, [fileType]: false }));
    }
  };

  const handlePreview = async (fileType) => {
    try {
      const res = await axios.get(`/api/files/preview/${USER_ID}/${fileType}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      window.open(url, "_blank");
    } catch {
      alert("Preview failed");
    }
  };

  const handleDelete = async (fileType) => {
    if (!window.confirm("Are you sure you want to delete this file?")) return;
    setLoading((prev) => ({ ...prev, [fileType]: true }));
    try {
      await axios.delete(`/api/files/delete/${USER_ID}/${fileType}`);
      setFiles((prev) => ({ ...prev, [fileType]: null }));
      alert("File deleted");
    } catch {
      alert("Delete failed");
    } finally {
      setLoading((prev) => ({ ...prev, [fileType]: false }));
    }
  };

  return (
    <Box sx={{ p: 2, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Typography variant="h4" mb={4} fontWeight={700} color="primary.dark">
        Job Descriptions & Resumes
      </Typography>
      <Grid container spacing={4} justifyContent="center" maxWidth={800}>
        {FILE_TYPES.map(({ key, label, icon }) => (
          <Grid item xs={12} md={6} key={key}>
            <Paper
              elevation={10}
              sx={{
                p: 4,
                textAlign: "center",
                borderRadius: 4,
                minHeight: 280,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                background: (theme) => theme.palette.background.paper,
                boxShadow: "0 8px 32px 0 rgba(41,121,255,0.10)",
                transition: "box-shadow 0.3s",
                "&:hover": {
                  boxShadow: "0 12px 48px 0 rgba(41,121,255,0.18)",
                }
              }}
            >
              <Avatar sx={{ bgcolor: "#2979ff", width: 64, height: 64, mb: 2, boxShadow: "0 2px 8px #2979ff44" }}>
                {icon}
              </Avatar>
              <Typography variant="h6" mb={2} fontWeight={600}>
                {label}
              </Typography>
              {loading[key] ? (
                <CircularProgress />
              ) : files[key] ? (
                <Stack direction="row" spacing={2} alignItems="center" justifyContent="center">
                  <Typography color="success.main" fontWeight={500}>
                    File uploaded.
                  </Typography>
                  <IconButton onClick={() => handlePreview(key)} color="primary" size="large">
                    <VisibilityIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(key)} color="error" size="large">
                    <DeleteIcon />
                  </IconButton>
                </Stack>
              ) : (
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<UploadFileIcon />}
                  sx={{ mt: 2, fontWeight: 600, fontSize: 16 }}
                >
                  Upload {label}
                  <input
                    type="file"
                    hidden
                    onChange={(e) => handleUpload(e, key)}
                    accept=".pdf,.doc,.docx"
                  />
                </Button>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}