import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import TransactionsPage from "./pages/TransactionsPage";
import PipelinePage from "./pages/PipelinePage";
import SubdivisionsPage from "./pages/SubdivisionsPage";
import SubdivisionDetailPage from "./pages/SubdivisionDetailPage";
import InventoryPage from "./pages/InventoryPage";
import PermitsPage from "./pages/PermitsPage";
import CommissionPage from "./pages/CommissionPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="review" element={<Navigate to="/transactions?unmatched_only=true" replace />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="permits" element={<PermitsPage />} />
        <Route path="commission" element={<CommissionPage />} />
        <Route path="pipeline" element={<PipelinePage />} />
        <Route path="subdivisions" element={<SubdivisionsPage />} />
        <Route path="subdivisions/:id" element={<SubdivisionDetailPage />} />
      </Route>
    </Routes>
  );
}
