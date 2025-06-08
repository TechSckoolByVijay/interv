import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#181f2a", // not extreme dark, soft dark blue/gray
      paper: "#232b3b",
      sidebar: "#202736"
    },
    primary: {
      main: "#2979ff" // Brighter blue
    },
    secondary: {
      main: "#ff4081" // Pink accent
    },
    success: {
      main: "#66bb6a"
    }
  },
  shape: {
    borderRadius: 14 // More rounded corners
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          boxShadow: "0 4px 24px 0 rgba(0,0,0,0.10)",
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          textTransform: "none",
          fontWeight: 600,
          fontSize: 16,
        }
      }
    }
  },
  typography: {
    fontFamily: "Inter, Roboto, Arial, sans-serif",
    h4: {
      fontWeight: 800,
      letterSpacing: 1,
    },
    h6: {
      fontWeight: 700,
    },
    body1: {
      fontWeight: 400,
    }
  }
});

export default theme;