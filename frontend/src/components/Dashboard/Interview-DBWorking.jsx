import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  Stack,
  CircularProgress,
  Snackbar,
  Alert,
  IconButton,
  BottomNavigation,
  BottomNavigationAction,
  Tooltip,
  LinearProgress,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import MicIcon from "@mui/icons-material/Mic";
import VideocamIcon from "@mui/icons-material/Videocam";
import ScreenShareIcon from "@mui/icons-material/ScreenShare";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import axios from "../../api";

// Dummy user id for demo; replace with real user context
const USER_ID = 1;

function useJDResumeStatus() {
  const [status, setStatus] = useState({ jd: false, resume: false, loading: true });
  useEffect(() => {
    let mounted = true;
    async function check() {
      try {
        await axios.get(`/api/files/preview/${USER_ID}/jd`, { responseType: "blob" });
        await axios.get(`/api/files/preview/${USER_ID}/resume`, { responseType: "blob" });
        if (mounted) setStatus({ jd: true, resume: true, loading: false });
      } catch {
        setStatus({ jd: false, resume: false, loading: false });
      }
    }
    check();
    return () => { mounted = false; };
  }, []);
  return status;
}

// --- Replace your AIQuestionAudio with this version ---
const AIQuestionAudio = React.forwardRef(({ text }, ref) => {
  const [playing, setPlaying] = useState(false);
  const utteranceRef = useRef(null);

  React.useImperativeHandle(ref, () => ({
    play: () => {
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const utter = new window.SpeechSynthesisUtterance(text);
      utter.onend = () => setPlaying(false);
      utter.onerror = () => setPlaying(false);
      utteranceRef.current = utter;
      setPlaying(true);
      window.speechSynthesis.speak(utter);
    },
    stop: () => {
      window.speechSynthesis.cancel();
      setPlaying(false);
    }
  }), [text]);

  useEffect(() => () => window.speechSynthesis.cancel(), [text]);

  return (
    <Tooltip title="AI Voice">
      <IconButton color="primary" onClick={() => ref.current.play()} size="large">
        <VolumeUpIcon fontSize="large" />
        {playing ? <PauseIcon /> : <PlayArrowIcon />}
      </IconButton>
    </Tooltip>
  );
});
// --- End AIQuestionAudio ---

function useContinuousMultiMediaRecorder() {
  const [recording, setRecording] = useState(false);
  const [streams, setStreams] = useState(null);
  const recordersRef = useRef({});
  const chunksRef = useRef({ audio: [], camera: [], screen: [], combined: [] });

  const getAllStreams = useCallback(async () => {
    if (streams) return streams;
    const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    setStreams({ audioStream, cameraStream, screenStream });
    return { audioStream, cameraStream, screenStream };
  }, [streams]);

  const start = useCallback(async () => {
    const { audioStream, cameraStream, screenStream } = await getAllStreams();
    const combinedStream = new MediaStream([
      ...audioStream.getAudioTracks(),
      ...cameraStream.getVideoTracks(),
      ...screenStream.getVideoTracks(),
    ]);

    const startRecorder = (stream, type) => {
      chunksRef.current[type] = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current[type].push(e.data);
      };
      recorder.start();
      recordersRef.current[type] = recorder;
    };

    startRecorder(audioStream, "audio");
    startRecorder(cameraStream, "camera");
    startRecorder(screenStream, "screen");
    startRecorder(combinedStream, "combined");

    setRecording(true);
  }, [getAllStreams]);

  // Stop all recorders and wait for data
  const stop = useCallback(() => {
    return new Promise((resolve) => {
      const types = ["audio", "camera", "screen", "combined"];
      let stopped = 0;
      types.forEach((type) => {
        const recorder = recordersRef.current[type];
        if (recorder && recorder.state === "recording") {
          recorder.onstop = () => {
            stopped += 1;
            if (stopped === types.length) resolve();
          };
          recorder.stop();
        } else {
          stopped += 1;
          if (stopped === types.length) resolve();
        }
      });
      setRecording(false);
    });
  }, []);

  // Wait for stop, then get blobs
  const getSegment = useCallback(async () => {
    await stop();
    const result = {};
    for (const type of ["audio", "camera", "screen", "combined"]) {
      result[type] = new Blob(chunksRef.current[type], { type: "video/webm" });
      chunksRef.current[type] = [];
    }
    return result;
  }, [stop]);

  useEffect(() => () => { stop(); }, [stop]);

  return { start, stop, recording, getSegment };
}

export default function Interview() {
  const [interviewName, setInterviewName] = useState("");
  const [interviewId, setInterviewId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, msg: "", severity: "info" });
  const [interviewDone, setInterviewDone] = useState(false);
  const jdResume = useJDResumeStatus();
  const [interviewStarted, setInterviewStarted] = useState(false);
  const audioRef = useRef();

  useEffect(() => {
    if (audioRef.current && typeof audioRef.current.play === "function") {
      audioRef.current.play();
    }
  }, [currentIdx]);

  const {
    start: startContinuousMulti,
    stop: stopContinuousMulti,
    recording: recordingContinuousMulti,
    getSegment: getSegmentContinuousMulti,
  } = useContinuousMultiMediaRecorder();

  const handleStartInterview = async () => {
    setLoading(true);
    try {
      console.log("[Interview] Starting interview with name:", interviewName);
      const res = await axios.post("/interview", { interview_name: interviewName });
      setInterviewId(res.data.id);
      const qres = await axios.post("/start_interview", {
        user_id: USER_ID,
        interview_id: res.data.id,
      });
      setQuestions(qres.data);
      setCurrentIdx(0);
      setInterviewStarted(true);
      console.log("[Interview] Questions loaded. Initializing media streams and recorders...");
      await startContinuousMulti();
      console.log("[Interview] Recording started for first question.");
      setSnackbar({ open: true, msg: "Interview started & recording!", severity: "success" });
    } catch (err) {
      console.error("[Interview] Failed to start interview:", err);
      setSnackbar({ open: true, msg: "Failed to start interview", severity: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (loading) return;
    setLoading(true);
    try {
      console.log(`[Interview] [Q${currentIdx + 1}] Stopping recording to upload answer...`);
      const blobs = await getSegmentContinuousMulti();
      console.log(`[Interview] [Q${currentIdx + 1}] Got blobs:`, {
        audio: blobs.audio?.size,
        camera: blobs.camera?.size,
        screen: blobs.screen?.size,
        combined: blobs.combined?.size,
      });

      for (const type of ["audio", "camera", "screen", "combined"]) {
        const blob = blobs[type];
        if (blob && blob.size > 0) {
          const fileName = `${USER_ID}-${interviewId}-${questions[currentIdx].question_id}_${type}.webm`;
          const formData = new FormData();
          formData.append("file", new File([blob], fileName, { type: "video/webm" }));
          try {
            console.log(`[Interview] [Q${currentIdx + 1}] Uploading ${type} file:`, fileName);
            const res = await axios.post(
              `/upload_answer/${USER_ID}/${interviewId}/${questions[currentIdx].question_id}/${type}`,
              formData
            );
            console.log(`[Interview] [Q${currentIdx + 1}] ${type} file uploaded:`, res.data);
          } catch (err) {
            console.error(`[Interview] [Q${currentIdx + 1}] Failed to upload ${type}:`, err);
          }
        } else {
          console.warn(`[Interview] [Q${currentIdx + 1}] ${type} blob is empty, skipping upload`);
        }
      }

      // Patch backend with file paths
      console.log(`[Interview] [Q${currentIdx + 1}] Patching backend with recording paths...`);
      await axios.patch(`/question/${questions[currentIdx].id}`, {
        audio_recording_path: `uploads/${USER_ID}/${interviewId}/${questions[currentIdx].question_id}_audio_${USER_ID}-${interviewId}-${questions[currentIdx].question_id}-audio.webm`,
        screen_recording_path: `uploads/${USER_ID}/${interviewId}/${questions[currentIdx].question_id}_screen_${USER_ID}-${interviewId}-${questions[currentIdx].question_id}-screen.webm`,
        camera_recording_path: `uploads/${USER_ID}/${interviewId}/${questions[currentIdx].question_id}_camera_${USER_ID}-${interviewId}-${questions[currentIdx].question_id}-camera.webm`,
        combined_recording_path: `uploads/${USER_ID}/${interviewId}/${questions[currentIdx].question_id}_combined_${USER_ID}-${interviewId}-${questions[currentIdx].question_id}-combined.webm`,
        status: "ATTEMPTED",
      });
      console.log(`[Interview] [Q${currentIdx + 1}] Backend patched successfully.`);

      setQuestions((prev) =>
        prev.map((q, i) =>
          i === currentIdx ? { ...q, status: "ATTEMPTED" } : q
        )
      );

      if (currentIdx < questions.length - 1) {
        setCurrentIdx((i) => i + 1);
        console.log(`[Interview] [Q${currentIdx + 2}] Starting recording for next question...`);
        await startContinuousMulti();
        console.log(`[Interview] [Q${currentIdx + 2}] Recording started.`);
      } else {
        console.log("[Interview] Fetching more questions...");
        const res = await axios.post("/more_questions", {
          user_id: USER_ID,
          interview_id: interviewId,
        });
        if (res.data.length === 0) {
          setInterviewDone(true);
          console.log("[Interview] No more questions. Stopping recording...");
          await stopContinuousMulti();
        } else {
          setQuestions((prev) => [...prev, ...res.data]);
          setCurrentIdx((i) => i + 1);
          console.log(`[Interview] [Q${currentIdx + 2}] Starting recording for next question...`);
          await startContinuousMulti();
          console.log(`[Interview] [Q${currentIdx + 2}] Recording started.`);
        }
      }
      setSnackbar({ open: true, msg: "Answer uploaded!", severity: "success" });
    } catch (err) {
      console.error(`[Interview] [Q${currentIdx + 1}] Upload or patch failed:`, err);
      setSnackbar({ open: true, msg: "Upload failed", severity: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleEndInterview = async () => {
    console.log("[Interview] Ending interview. Stopping all recordings...");
    await stopContinuousMulti();
    setInterviewDone(true);
    setSnackbar({ open: true, msg: "Interview ended.", severity: "info" });
  };

  // UI: Start page
  if (!interviewId || !interviewStarted) {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", mt: 6 }}>
        <Paper elevation={8} sx={{ p: 4, borderRadius: 4 }}>
          <Typography variant="h4" color="primary" fontWeight={800} mb={2}>
            Start New Interview
          </Typography>
          <TextField
            label="Interview Name"
            value={interviewName}
            onChange={(e) => setInterviewName(e.target.value)}
            fullWidth
            sx={{ mb: 3 }}
            disabled={loading}
          />
          <Stack direction="row" spacing={2} alignItems="center" mb={2}>
            <CheckCircleIcon color={jdResume.jd ? "success" : "disabled"} />
            <Typography>JD Uploaded</Typography>
            <CheckCircleIcon color={jdResume.resume ? "success" : "disabled"} />
            <Typography>Resume Uploaded</Typography>
          </Stack>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddCircleOutlineIcon />}
            disabled={
              !interviewName ||
              !jdResume.jd ||
              !jdResume.resume ||
              loading ||
              jdResume.loading
            }
            onClick={handleStartInterview}
            sx={{ fontWeight: 700, fontSize: 18, px: 4, py: 1.5 }}
          >
            {loading ? <CircularProgress size={24} /> : "Start Interview"}
          </Button>
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

  // UI: Interview done
  if (interviewDone) {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", mt: 8, textAlign: "center" }}>
        <CheckCircleIcon color="success" sx={{ fontSize: 80, mb: 2 }} />
        <Typography variant="h4" fontWeight={800} color="success.main" mb={2}>
          Congratulations!
        </Typography>
        <Typography mb={3}>
          Your interview is complete. Your report is being prepared.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          href="/performance"
        >
          Go to Performance Tab
        </Button>
      </Box>
    );
  }

  // UI: Interview flow
  const q = questions[currentIdx];
  const morePending = questions.some((q, idx) => q.status === "NEW" && idx > currentIdx);

  if (!questions.length || !q) {
    // Show loading or a friendly message
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", mt: 8, textAlign: "center" }}>
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="h6">Loading questions...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 700, mx: "auto", mt: 4 }}>
      <Paper elevation={10} sx={{ p: 4, borderRadius: 4, mb: 2 }}>
        <Stack direction="row" alignItems="center" spacing={2} mb={2}>
          <AIQuestionAudio ref={audioRef} text={q.question_text} />
          <Typography variant="h6" fontWeight={700}>
            Question {currentIdx + 1}:
          </Typography>
        </Stack>
        <Typography variant="body1" sx={{ mb: 3, fontSize: 20 }}>
          {q.question_text}
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center" mb={2}>
          <Tooltip title="Recording Audio">
            <MicIcon color={recordingContinuousMulti ? "primary" : "disabled"} />
          </Tooltip>
          <Tooltip title="Recording Camera">
            <VideocamIcon color={recordingContinuousMulti ? "primary" : "disabled"} />
          </Tooltip>
          <Tooltip title="Recording Screen">
            <ScreenShareIcon color={recordingContinuousMulti ? "primary" : "disabled"} />
          </Tooltip>
          <Typography sx={{ ml: 2, fontWeight: 700 }}>
            {recordingContinuousMulti ? "Recording..." : "Not Recording"}
          </Typography>
        </Stack>
        <LinearProgress
          variant="determinate"
          value={((currentIdx + 1) / questions.length) * 100}
          sx={{ mb: 2 }}
        />
        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
          <Typography color="text.secondary">
            {morePending && "More pending questions available"}
          </Typography>
          <Button
            variant="contained"
            endIcon={<ArrowForwardIcon />}
            onClick={handleNext}
            disabled={loading || interviewDone}
          >
            {loading ? <CircularProgress size={20} /> : "Next"}
          </Button>
          <Button
            variant="outlined"
            color="error"
            onClick={handleEndInterview}
            disabled={loading || !recordingContinuousMulti}
          >
            End Interview
          </Button>
        </Stack>
      </Paper>
      <BottomNavigation
        showLabels
        value={currentIdx}
        sx={{
          borderRadius: 3,
          boxShadow: 2,
          background: "#232b3b",
          mb: 2,
        }}
      >
        {questions.map((q, idx) => (
          <BottomNavigationAction
            key={q.id}
            label={idx + 1}
            icon={
              q.status === "ATTEMPTED" ? (
                <CheckCircleIcon color="success" />
              ) : (
                <PlayArrowIcon />
              )
            }
            sx={{
              color: idx === currentIdx ? "primary.main" : "text.secondary",
              fontWeight: idx === currentIdx ? 700 : 400,
            }}
            onClick={() => setCurrentIdx(idx)}
          />
        ))}
      </BottomNavigation>
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