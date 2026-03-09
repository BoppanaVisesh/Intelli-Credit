import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ApplicationDetail from './pages/ApplicationDetail';
import CAMViewer from './pages/CAMViewer';
import Dashboard from './pages/Dashboard';
import DataIngestion from './pages/DataIngestion';
import DueDiligencePortal from './pages/DueDiligencePortal';
import FraudDetection from './pages/FraudDetection';
import NewApplication from './pages/NewApplication';
import ResearchAgent from './pages/ResearchAgent';
import ScoringResult from './pages/ScoringResult';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-application" element={<NewApplication />} />
          <Route path="/application/:id" element={<ApplicationDetail />} />
          <Route path="/application/:id/ingestion" element={<DataIngestion />} />
          <Route path="/application/:id/research" element={<ResearchAgent />} />
          <Route path="/application/:id/fraud" element={<FraudDetection />} />
          <Route path="/application/:id/scoring" element={<ScoringResult />} />
          <Route path="/application/:id/cam" element={<CAMViewer />} />
          <Route path="/application/:id/due-diligence" element={<DueDiligencePortal />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
