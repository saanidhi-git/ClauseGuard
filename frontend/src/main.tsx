import { StrictMode, Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import Layout from "./components/Layout";
import { ToastProvider } from "./components/Toast";
import Home from "./pages/Home";
import Report from "./pages/Report";
import HistoryPage from "./pages/History";
import About from "./pages/About";
import NotFound from "./pages/NotFound";

// charts are heavy, so load this page only when needed
const Insights = lazy(() => import("./pages/Insights"));

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/report/:id" element={<Report />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/insights" element={<Suspense fallback={<div className="mx-auto max-w-7xl px-4 py-8"><div className="skeleton h-72" /></div>}><Insights /></Suspense>} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  </StrictMode>,
);
