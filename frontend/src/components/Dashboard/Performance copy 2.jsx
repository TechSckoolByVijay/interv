import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Stack,
  Snackbar,
  Alert,
  Avatar,
  Chip,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from "@mui/material";
import VisibilityIcon from '@mui/icons-material/Visibility';
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import BarChartIcon from "@mui/icons-material/BarChart";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import axios from "../../api";

const USER_ID = JSON.parse(localStorage.getItem("user_data"))?.id;

const statusColors = {
  NEW: "info",
  AI_EVALUATION_DONE: "success",
};

function InterviewSummaryCard({ summary, onViewDetails }) {
  const statusColor = summary.status === 'AI_EVALUATION_DONE' ? 'success' : 'info';

  return (
    <Paper
      elevation={10}
      sx={{
        p: 3,
        borderRadius: 4,
        minWidth: 320,
        maxWidth: 380,
        background: (theme) => theme.palette.background.paper,
        border: "2px solid #2979ff",
        boxShadow: "0 8px 32px 0 rgba(41,121,255,0.10)",
        transition: "transform 0.2s, box-shadow 0.2s",
        "&:hover": {
          transform: "translateY(-6px) scale(1.03)",
          boxShadow: "0 12px 36px 0 rgba(41,121,255,0.18)",
        },
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Avatar sx={{ bgcolor: "#2979ff", width: 56, height: 56, mb: 2, boxShadow: "0 2px 8px #2979ff44" }}>
        <BarChartIcon fontSize="large" />
      </Avatar>
      <Typography variant="h6" fontWeight={800} color="primary.main" mb={1}>
        {summary.interview_name}
      </Typography>
      <Chip
        label={summary.status.replace(/_/g, ' ')}
        color={statusColor}
        size="small"
        sx={{
          fontWeight: 700,
          borderRadius: 1,
          border: '1.5px solid #2979ff',
          color: "#2979ff",
          background: statusColor === 'success' ? '#e8f5e9' : '#e3f2fd',
          mb: 1,
        }}
      />
      <Typography variant="body2" color="text.secondary" mb={1}>
        Interview ID: <b>{summary.id}</b>
      </Typography>
      {summary.score_in_percentage && (
        <Typography variant="body1" sx={{ color: "#2979ff", fontWeight: 700 }} mb={0.5}>
          Score: {summary.score_in_percentage}%
        </Typography>
      )}
      {summary.interview_cleared_by_candidate && (
        <Typography variant="body2" sx={{ color: "#66bb6a", fontWeight: 600 }} mb={2}>
          Result: <b>{summary.interview_cleared_by_candidate}</b>
        </Typography>
      )}
      <Button
        variant="contained"
        sx={{
          mt: 2,
          borderRadius: 2,
          fontWeight: 700,
          textTransform: 'none',
          background: "#2979ff",
          color: "#fff",
          boxShadow: "0 2px 8px 0 rgba(41,121,255,0.10)",
          '&:hover': { background: "#1565c0" },
        }}
        startIcon={<VisibilityIcon />}
        fullWidth
        onClick={() => onViewDetails(summary.id)}
      >
        View Details
      </Button>
    </Paper>
  );
}

export default function Performance() {
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInterviewId, setSelectedInterviewId] = useState(null);
  const [interviewDetails, setInterviewDetails] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, msg: "", severity: "info" });

  useEffect(() => {
    async function fetchInterviews() {
      setLoading(true);
      try {
        const res = await axios.get(`/api/performance/interviews/${USER_ID}`);
        setInterviews(res.data);
      } catch (err) {
        setInterviews([]);
        setSnackbar({ open: true, msg: "Failed to load interviews", severity: "error" });
      }
      setLoading(false);
    }
    fetchInterviews();
  }, []);

  useEffect(() => {
    if (selectedInterviewId) {
      setLoading(true);
      axios
        .get(`/api/performance/interview/${selectedInterviewId}/details`)
        .then((res) => setInterviewDetails(res.data))
        .catch(() => {
          setInterviewDetails(null);
          setSnackbar({ open: true, msg: "Failed to load interview details", severity: "error" });
        })
        .finally(() => setLoading(false));
    }
  }, [selectedInterviewId]);

  if (loading) {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", mt: 8, textAlign: "center" }}>
        <CircularProgress sx={{ mb: 2, color: "#2979ff" }} />
        <Typography variant="h6" color="#2979ff">Loading...</Typography>
      </Box>
    );
  }

  // FIX: Return interview details UI if selected
  if (interviewDetails && selectedInterviewId) {
    const { interview, questions } = interviewDetails;
    return (
      <Box sx={{ maxWidth: 900, mx: "auto", mt: 4 }}>
        {/* Header and summary */}
        <Paper
          elevation={10}
          sx={{
            p: 5,
            borderRadius: 4,
            background: (theme) => theme.palette.background.paper,
            border: "2px solid #2979ff",
          }}
        >
          <Stack direction="row" alignItems="center" spacing={2} mb={2}>
            <IconButton
              onClick={() => {
                setSelectedInterviewId(null);
                setInterviewDetails(null);
              }}
            >
              <ArrowBackIcon sx={{ color: "#2979ff" }} />
            </IconButton>
            <Typography variant="h5" fontWeight={800} color="primary.main">
              Interview: {interview.interview_name}
            </Typography>
            <Chip
              label={interview.status.replace(/_/g, " ")}
              color={statusColors[interview.status] || "default"}
              sx={{
                ml: 2,
                fontWeight: 700,
                color: "#2979ff",
                border: "1.5px solid #2979ff",
              }}
            />
          </Stack>
          <Divider sx={{ my: 2 }} />
          <Stack direction="row" spacing={3} mb={3}>
            {interview.score_in_percentage && (
              <Chip
                label={`Score: ${interview.score_in_percentage}%`}
                color="primary"
                sx={{ fontWeight: 700, fontSize: 16 }}
              />
            )}
            {interview.interview_cleared_by_candidate && (
              <Chip
                label={`Result: ${interview.interview_cleared_by_candidate}`}
                color={
                  interview.interview_cleared_by_candidate === "Cleared"
                    ? "success"
                    : "warning"
                }
                sx={{ fontWeight: 700, fontSize: 16 }}
              />
            )}
          </Stack>
          <Typography variant="h6" mb={2} color="primary.light">
            Questions & Answers
          </Typography>
          <List>
            {questions.map((qa, idx) => (
              <Paper
                key={qa.id}
                elevation={4}
                sx={{
                  mb: 3,
                  p: 3,
                  borderRadius: 3,
                  background: "#181f2a",
                  boxShadow: "0 2px 8px #2979ff22",
                }}
              >
                <Stack direction="row" alignItems="center" spacing={2} mb={1}>
                  <Typography
                    variant="subtitle1"
                    fontWeight={700}
                    color="primary.light"
                    sx={{ minWidth: 90 }}
                  >
                    Q{idx + 1}
                  </Typography>
                  <Typography
                    variant="body1"
                    fontWeight={700}
                    sx={{
                      color: "#fff",
                      background: "#22304a",
                      borderRadius: 2,
                      px: 2,
                      py: 1,
                      fontSize: 18,
                      flex: 1,
                    }}
                  >
                    {qa.question_text}
                  </Typography>
                </Stack>
                <Divider sx={{ mb: 1, background: "#22304a" }} />
                <Typography
                  variant="body2"
                  sx={{
                    whiteSpace: "pre-line",
                    wordBreak: "break-word",
                    background: "#232e43",
                    p: 2,
                    borderRadius: 2,
                    mb: 1,
                    fontSize: 17,
                    color: "#fff",
                  }}
                >
                  <b>A:</b>{" "}
                  {qa.answer_text ? (
                    qa.answer_text
                  ) : (
                    <i style={{ color: "#888" }}>No answer recorded</i>
                  )}
                </Typography>
                {qa.combined_recording_path && (
                  <Box sx={{ my: 1 }}>
                    <audio
                      controls
                      src={qa.combined_recording_path}
                      style={{
                        width: "100%",
                        background: "#22304a",
                        borderRadius: 8,
                        marginTop: 8,
                      }}
                    >
                      Your browser does not support the audio element.
                    </audio>
                  </Box>
                )}
                {qa.ai_remark && (
                  <Typography
                    variant="body2"
                    sx={{
                      background: "#e3f2fd",
                      p: 1.5,
                      borderRadius: 2,
                      mb: 1,
                      color: "#1565c0",
                    }}
                  >
                    <b>AI Remark:</b> {qa.ai_remark}
                  </Typography>
                )}
                <Stack direction="row" spacing={2} mt={1}>
                  {qa.candidate_score !== null && (
                    <Chip
                      label={`Score: ${qa.candidate_score}`}
                      color="primary"
                      size="small"
                    />
                  )}
                  {qa.candidate_grade && (
                    <Chip
                      label={`Grade: ${qa.candidate_grade}`}
                      color="success"
                      size="small"
                    />
                  )}
                  <Chip
                    label={qa.status.replace(/_/g, " ")}
                    color={qa.status === "ATTEMPTED" ? "success" : "info"}
                    size="small"
                  />
                  {qa.combined_recording_path && (
                    <Chip
                      label="Answer Audio Extracted"
                      color="info"
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Stack>
              </Paper>
            ))}
          </List>
        </Paper>
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        >
          <Alert severity={snackbar.severity}>{snackbar.msg}</Alert>
        </Snackbar>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        maxWidth: 1200,
        mx: "auto",
        mt: 4,
        mb: 4,
        background: (theme) => theme.palette.background.default,
        borderRadius: 4,
        p: 3,
      }}
    >
      <Paper elevation={10} sx={{ p: 5, borderRadius: 4, mb: 3, background: (theme) => theme.palette.background.paper }}>
        <Stack direction="row" alignItems="center" spacing={2} mb={2}>
          <BarChartIcon sx={{ fontSize: 48, color: "#2979ff" }} />
          <Typography variant="h4" fontWeight={800} color="primary.main">
            Interview Performance Summary
          </Typography>
        </Stack>
        <Divider sx={{ mb: 3 }} />
      <Grid container spacing={4} justifyContent="center">
        {interviews.length === 0 ? (
          <Grid item xs={12}>
            <Typography color="text.secondary" align="center">
              No interviews found.
            </Typography>
          </Grid>
        ) : (
          interviews.map((summary) => (
            <Grid item xs={12} sm={6} md={4} key={summary.id}>
              <InterviewSummaryCard summary={summary} onViewDetails={setSelectedInterviewId} />
            </Grid>
          ))
        )}
      </Grid>
      </Paper>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
      >
        <Alert severity={snackbar.severity}>{snackbar.msg}</Alert>
      </Snackbar>
    </Box>
  );
}