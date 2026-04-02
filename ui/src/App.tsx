import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import TransactionsPage from "./pages/TransactionsPage";
import ReviewPage from "./pages/ReviewPage";
import PipelinePage from "./pages/PipelinePage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="review" element={<ReviewPage />} />
        <Route path="pipeline" element={<PipelinePage />} />
      </Route>
    </Routes>
  );
}
