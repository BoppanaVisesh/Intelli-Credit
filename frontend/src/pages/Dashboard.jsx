import { AlertCircle, CheckCircle, FileText, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { DECISION_LABELS } from '../utils/constants';
import { formatCurrency, formatDate, getDecisionBadgeClass } from '../utils/formatters';

const Dashboard = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
  });

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      setLoading(true);
      const data = await api.getApplications();
      setApplications(data.applications);
      
      // Calculate stats
      const stats = {
        total: data.total,
        pending: data.applications.filter(a => a.status === 'PENDING' || a.status === 'PROCESSING').length,
        approved: data.applications.filter(a => a.decision === 'APPROVE').length,
        rejected: data.applications.filter(a => a.decision === 'REJECT').length,
      };
      setStats(stats);
    } catch (error) {
      console.error('Failed to load applications:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <Link to="/new-application" className="btn-primary">
          New Application
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Applications</p>
              <p className="text-3xl font-bold mt-2">{stats.total}</p>
            </div>
            <FileText className="text-blue-600" size={32} />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pending</p>
              <p className="text-3xl font-bold mt-2">{stats.pending}</p>
            </div>
            <AlertCircle className="text-yellow-600" size={32} />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Approved</p>
              <p className="text-3xl font-bold mt-2">{stats.approved}</p>
            </div>
            <CheckCircle className="text-green-600" size={32} />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Rejected</p>
              <p className="text-3xl font-bold mt-2">{stats.rejected}</p>
            </div>
            <TrendingUp className="text-red-600" size={32} />
          </div>
        </div>
      </div>

      {/* Applications Table */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Recent Applications</h2>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : applications.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText size={48} className="mx-auto mb-4 text-gray-400" />
            <p>No applications yet. Create your first application to get started.</p>
            <Link to="/new-application" className="btn-primary mt-4 inline-block">
              Create Application
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Application ID</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Company</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Sector</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Requested</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Score</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Decision</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr key={app.application_id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{app.application_id}</td>
                    <td className="py-3 px-4">{app.company_name}</td>
                    <td className="py-3 px-4">{app.sector}</td>
                    <td className="py-3 px-4">{formatCurrency(app.requested_limit_cr)}</td>
                    <td className="py-3 px-4">
                      {app.final_score ? (
                        <span className={`font-bold ${app.final_score >= 75 ? 'text-green-600' : app.final_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {app.final_score}/100
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {app.decision ? (
                        <span className={`badge ${getDecisionBadgeClass(app.decision)}`}>
                          {DECISION_LABELS[app.decision]}
                        </span>
                      ) : (
                        <span className="badge bg-gray-100 text-gray-800">Pending</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{formatDate(app.created_at)}</td>
                    <td className="py-3 px-4">
                      <Link
                        to={`/application/${app.application_id}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
