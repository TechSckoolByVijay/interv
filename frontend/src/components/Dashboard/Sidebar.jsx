import React from "react";
import { NavLink } from "react-router-dom";
import {
  List,
  ListItemIcon,
  ListItemText,
  Drawer,
  ListItemButton,
  Toolbar,
  Box,
  Typography,
} from "@mui/material";
import AssignmentIcon from "@mui/icons-material/Assignment";
import DescriptionIcon from "@mui/icons-material/Description";
import BarChartIcon from "@mui/icons-material/BarChart";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";

const drawerWidth = 220;

const navItems = [
  { text: "Interview", icon: <AssignmentIcon />, path: "/interview" },
  { text: "JD & Resume", icon: <DescriptionIcon />, path: "/jd-resume" },
  { text: "Performance", icon: <BarChartIcon />, path: "/performance" },
  { text: "Support", icon: <SupportAgentIcon />, path: "/support" },
];

export default function Sidebar() {
  return (
    <Drawer
      variant="permanent"
      anchor="left"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
          background: "linear-gradient(180deg, #202736 80%, #2979ff 100%)",
          borderRight: "none",
          boxShadow: "2px 0 16px 0 rgba(41,121,255,0.08)",
        },
      }}
    >
      <Toolbar>
        <Box sx={{ width: "100%", textAlign: "center", py: 1 }}>
          <img src="/logo192.png" alt="Logo" style={{ width: 48, marginBottom: 8 }} />
          <Typography variant="h6" color="primary.contrastText" fontWeight={800}>
            AI Interviewer
          </Typography>
        </Box>
      </Toolbar>
      <List sx={{ mt: 2 }}>
        {navItems.map((item) => (
          <ListItemButton
            key={item.text}
            component={NavLink}
            to={item.path}
            sx={{
              color: "white",
              "&.active": {
                background: "rgba(41,121,255,0.15)",
                color: "#fff",
                fontWeight: "bold",
                borderLeft: "4px solid #2979ff",
              },
              "&:hover": {
                background: "rgba(41,121,255,0.10)",
              },
              mt: 1,
              borderRadius: 2,
              mx: 1,
            }}
          >
            <ListItemIcon sx={{ color: "inherit" }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
}