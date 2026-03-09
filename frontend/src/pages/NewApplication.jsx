import { AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const NewApplication = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    company_name: '',
    mca_cin: '',
    sector: '',
    requested_limit_cr: '',
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await api.createApplication({
        company_name: formData.company_name,
        mca_cin: formData.mca_cin,
        sector: formData.sector,
        requested_limit_cr: parseFloat(formData.requested_limit_cr),
      });
      navigate(`/application/${result.application_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">New Credit Application</h1>
        <p className="text-gray-600 mt-2">
          Enter company details to start the credit appraisal pipeline
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Company Details</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Company Name *</label>
              <input type="text" name="company_name" value={formData.company_name}
                onChange={handleInputChange} required placeholder="e.g., SpiceJet Limited" className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">MCA CIN *</label>
              <input type="text" name="mca_cin" value={formData.mca_cin}
                onChange={handleInputChange} required placeholder="e.g., L51909DL1984PLC018603" className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sector *</label>
              <select name="sector" value={formData.sector} onChange={handleInputChange} required className="input-field">
                <option value="">Select Sector</option>
                <option value="Aviation">Aviation</option>
                <option value="IT Services">IT Services</option>
                <option value="Industrial Manufacturing">Industrial Manufacturing</option>
                <option value="Textiles">Textiles</option>
                <option value="Pharmaceuticals">Pharmaceuticals</option>
                <option value="Real Estate">Real Estate</option>
                <option value="Banking">Banking</option>
                <option value="FMCG">FMCG</option>
                <option value="Auto Components">Auto Components</option>
                <option value="Food Processing">Food Processing</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Requested Limit (Cr) *</label>
              <input type="number" step="0.01" name="requested_limit_cr" value={formData.requested_limit_cr}
                onChange={handleInputChange} required placeholder="e.g., 500" className="input-field" />
            </div>
          </div>
        </div>

        {/* Pipeline Info */}
        <div className="card bg-blue-50 border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">What happens next?</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2 text-sm text-blue-800">
            <div className="flex items-center gap-2"><span className="font-bold">1.</span> Upload Documents</div>
            <div className="flex items-center gap-2"><span className="font-bold">2.</span> External Intelligence</div>
            <div className="flex items-center gap-2"><span className="font-bold">3.</span> Primary Insights</div>
            <div className="flex items-center gap-2"><span className="font-bold">4.</span> Credit Scoring</div>
            <div className="flex items-center gap-2"><span className="font-bold">5.</span> Generate CAM</div>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-4">
          <button type="button" onClick={() => navigate('/')} className="btn-secondary" disabled={loading}>Cancel</button>
          <button type="submit" className="btn-primary flex items-center space-x-2" disabled={loading}>
            {loading ? (
              <><div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div><span>Creating...</span></>
            ) : (
              <span>Create Application</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default NewApplication;
