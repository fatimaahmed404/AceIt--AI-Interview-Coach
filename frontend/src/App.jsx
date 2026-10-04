import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Record from "./pages/Record";
import Results from "./pages/Results";
import History from "./pages/History";
import Dashboard from "./pages/Dashboard";
import Mock from "./pages/Mock";
import ModelInfo from "./pages/ModelInfo";
import Comparison from "./pages/Comparison";
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/record" element={<Record />} />
        <Route path="/results" element={<Results />} />
        <Route path="/history" element={<History />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/mock" element={<Mock />} />
        <Route path="/model-info" element={<ModelInfo />} />
        <Route path="/comparison" element={<Comparison />} />
      </Routes>
    </BrowserRouter>
  );
}
