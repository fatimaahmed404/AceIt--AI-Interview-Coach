import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute, GuestRoute } from "./auth/RouteGuards";

import Home from "./pages/Home";
import Record from "./pages/Record";
import Results from "./pages/Results";
import History from "./pages/History";
import Dashboard from "./pages/Dashboard";
import Mock from "./pages/Mock";
import ModelInfo from "./pages/ModelInfo";
import Comparison from "./pages/Comparison";
import Navbar from "./components/Navbar";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import VerifyEmail from "./pages/VerifyEmail";
import ForgotPassword from "./pages/ForgotPassword";
import VerifyResetCode from "./pages/VerifyResetCode";
import ResetPassword from "./pages/ResetPassword";
import Account from "./pages/Account";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          {/* Guest-only auth pages */}
          <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
          <Route path="/signup" element={<GuestRoute><Signup /></GuestRoute>} />
          <Route path="/forgot-password" element={<GuestRoute><ForgotPassword /></GuestRoute>} />
          <Route path="/verify-reset-code" element={<GuestRoute><VerifyResetCode /></GuestRoute>} />
          <Route path="/reset-password" element={<GuestRoute><ResetPassword /></GuestRoute>} />
          {/* Verify-email is reachable whether or not logged in */}
          <Route path="/verify-email" element={<VerifyEmail />} />

          {/* Protected application */}
          <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/record" element={<ProtectedRoute><Record /></ProtectedRoute>} />
          <Route path="/results" element={<ProtectedRoute><Results /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/mock" element={<ProtectedRoute><Mock /></ProtectedRoute>} />
          <Route path="/account" element={<ProtectedRoute><Account /></ProtectedRoute>} />

          {/* Public informational pages */}
          <Route path="/model-info" element={<ModelInfo />} />
          <Route path="/comparison" element={<Comparison />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
