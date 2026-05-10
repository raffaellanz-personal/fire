import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./styles/variables.css";
import "./App.css";

import Sidebar from "./components/Sidebar";

import DashboardPage from "./pages/DashboardPage";
import TimelinePage from "./pages/TimelinePage";
import EmailsPage from "./pages/EmailsPage";
import EmailDetailPage from "./pages/EmailDetailPage";
import ThreadsPage from "./pages/ThreadsPage";
import DocumentsPage from "./pages/DocumentsPage";
import IssuesPage from "./pages/IssuesPage";
import LawsPage from "./pages/LawsPage";
import StrategyPage from "./pages/StrategyPage";
import EventDetailPage from "./pages/EventDetailPage";

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="appLayout">
      <Sidebar />
      <main className="mainContent">
        <div className="page">{children}</div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <DashboardPage />
            </Layout>
          }
        />
        <Route
          path="/timeline"
          element={
            <Layout>
              <TimelinePage />
            </Layout>
          }
        />
        <Route
          path="/emails"
          element={
            <Layout>
              <EmailsPage />
            </Layout>
          }
        />
        <Route
          path="/emails/:id"
          element={
            <Layout>
              <EmailDetailPage />
            </Layout>
          }
        />
        <Route
          path="/threads"
          element={
            <Layout>
              <ThreadsPage />
            </Layout>
          }
        />
        <Route
          path="/timeline/:id"
          element={
            <Layout>
              <EventDetailPage />
            </Layout>
          }
        />
        <Route
          path="/documents"
          element={
            <Layout>
              <DocumentsPage />
            </Layout>
          }
        />
        <Route
          path="/issues"
          element={
            <Layout>
              <IssuesPage />
            </Layout>
          }
        />
        <Route
          path="/laws"
          element={
            <Layout>
              <LawsPage />
            </Layout>
          }
        />
        <Route
          path="/strategy"
          element={
            <Layout>
              <StrategyPage />
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
