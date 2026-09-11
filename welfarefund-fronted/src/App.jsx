import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

import AdminAuth from './pages/admin/AdminAuth';
import AdminProfile from './pages/admin/AdminProfile';
import AdminPaymentSettings from './pages/admin/AdminPaymentSettings';
import AdminPayments from './pages/admin/AdminPayments';
import AdminWithdrawals from './pages/admin/AdminWithdrawals';

import UserAuth from './pages/user/UserAuth';
import UserProfile from './pages/user/UserProfile';
import UserDashboard from './pages/user/UserDashboard';
import UserPayments from './pages/user/UserPayments';
import UserWithdrawals from './pages/user/UserWithdrawals';

import './App.css';

function Home() {
  return (
    <div>
      <h1>Welfare Fund API Navigation</h1>
      <ul>
        <li><Link to="/api/admin/authentication">Admin Authentication</Link></li>
        <li><Link to="/api/admin/profile">Admin Profile</Link></li>
        <li><Link to="/api/admin/payments-settings">Admin Payment Settings</Link></li>
        <li><Link to="/api/admin/payments">Admin Payments</Link></li>
        <li><Link to="/api/admin/withdrawals">Admin Withdrawals</Link></li>
        <li><Link to="/api/user/authentication">User Authentication</Link></li>
        <li><Link to="/api/user/profile">User Profile</Link></li>
        <li><Link to="/api/user/dashboard">User Dashboard</Link></li>
        <li><Link to="/api/user/payments">User Payments</Link></li>
        <li><Link to="/api/user/withdrawals">User Withdrawals</Link></li>
      </ul>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />

        {/* Admin Routes */}
        <Route path="/api/admin/authentication" element={<AdminAuth />} />
        <Route path="/api/admin/profile" element={<AdminProfile />} />
        <Route path="/api/admin/payments-settings" element={<AdminPaymentSettings />} />
        <Route path="/api/admin/payments" element={<AdminPayments />} />
        <Route path="/api/admin/withdrawals" element={<AdminWithdrawals />} />

        {/* User Routes */}
        <Route path="/api/user/authentication" element={<UserAuth />} />
        <Route path="/api/user/profile" element={<UserProfile />} />
        <Route path="/api/user/dashboard" element={<UserDashboard />} />
        <Route path="/api/user/payments" element={<UserPayments />} />
        <Route path="/api/user/withdrawals" element={<UserWithdrawals />} />
      </Routes>
    </Router>
  );
}

export default App;
