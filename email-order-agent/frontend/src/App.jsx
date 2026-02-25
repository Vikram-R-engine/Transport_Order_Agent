import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Nav from "./components/Nav";
import Dashboard from "./pages/Dashboard";
import Inbox from "./pages/Inbox";
import EmailDetail from "./pages/EmailDetail";
import ReviewQueue from "./pages/ReviewQueue";
import Orders from "./pages/Orders";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import Activity from "./pages/Activity";

function Private({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/*"
          element={
            <Private>
              <Nav />
              <div style={{ padding: 16, maxWidth: 1100, margin: "0 auto" }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/inbox" element={<Inbox />} />
                  <Route path="/emails/:id" element={<EmailDetail />} />
                  <Route path="/review" element={<ReviewQueue />} />
                  <Route path="/orders" element={<Orders />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/activity" element={<Activity />} />
                </Routes>
              </div>
            </Private>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}