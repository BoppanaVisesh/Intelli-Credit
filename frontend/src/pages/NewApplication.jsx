import { AlertCircle, FileText, Upload } from 'lucide-react';
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
    credit_officer_notes: '',
  });

  const [files, setFiles] = useState({
    annual_report: null,
    bank_statements: null,
    gst_returns: null,
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e, fileType) => {
    const file = e.target.files[0];
    setFiles(prev => ({ ...prev, [fileType]: file }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Create FormData for file upload
      const formDataObj = new FormData();
      formDataObj.append('company_name', formData.company_name);
      formDataObj.append('mca_cin', formData.mca_cin);
      formDataObj.append('sector', formData.sector);
      formDataObj.append('requested_limit_cr', formData.requested_limit_cr);
      
      if (formData.credit_officer_notes) {
        formDataObj.append('credit_officer_notes', formData.credit_officer_notes);
      }

      if (files.annual_report) {
        formDataObj.append('annual_report', files.annual_report);
      }
      if (files.bank_statements) {
        formDataObj.append('bank_statements', files.bank_statements);
      }
      if (files.gst_returns) {
        formDataObj.append('gst_returns', files.gst_returns);
      }

      // Call the analyze-credit endpoint
      const result = await api.analyzeCreditApplication(formDataObj);

      // Navigate to the application detail page
      navigate(`/application/${result.application_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create application');
      console.error('Error creating application:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">New Credit Application</h1>
        <p className="text-gray-600 mt-2">
          Upload documents and company details to generate a comprehensive credit appraisal
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
        {/* Company Details Card */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Company Details</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Name *
              </label>
              <input
                type="text"
                name="company_name"
                value={formData.company_name}
                onChange={handleInputChange}
                required
                placeholder="e.g., Apex Manufacturing Pvt Ltd"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                MCA CIN *
              </label>
              <input
                type="text"
                name="mca_cin"
                value={formData.mca_cin}
                onChange={handleInputChange}
                required
                placeholder="e.g., U28920MH2018PTC31254"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sector *
              </label>
              <select
                name="sector"
                value={formData.sector}
                onChange={handleInputChange}
                required
                className="input-field"
              >
                <option value="">Select Sector</option>
                <option value="Industrial Manufacturing">Industrial Manufacturing</option>
                <option value="Textiles">Textiles</option>
                <option value="Pharmaceuticals">Pharmaceuticals</option>
                <option value="Auto Components">Auto Components</option>
                <option value="Food Processing">Food Processing</option>
                <option value="IT Services">IT Services</option>
                <option value="Construction">Construction</option>
                <option value="Trading">Trading</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Requested Limit (₹ Crores) *
              </label>
              <input
                type="number"
                step="0.01"
                name="requested_limit_cr"
                value={formData.requested_limit_cr}
                onChange={handleInputChange}
                required
                placeholder="e.g., 10.00"
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Document Upload Card */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Upload Documents</h2>
          <p className="text-sm text-gray-600 mb-4">
            Upload financial documents for automated analysis
          </p>

          <div className="space-y-4">
            <FileUploadField
              label="Annual Report (PDF)"
              accept=".pdf"
              file={files.annual_report}
              onChange={(e) => handleFileChange(e, 'annual_report')}
            />

            <FileUploadField
              label="Bank Statements (PDF/Excel)"
              accept=".pdf,.xlsx,.xls,.csv"
              file={files.bank_statements}
              onChange={(e) => handleFileChange(e, 'bank_statements')}
            />

            <FileUploadField
              label="GST Returns (PDF/Excel)"
              accept=".pdf,.xlsx,.xls,.csv,.json"
              file={files.gst_returns}
              onChange={(e) => handleFileChange(e, 'gst_returns')}
            />
          </div>
        </div>

        {/* Due Diligence Notes Card */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Due Diligence Notes (Optional)</h2>
          <p className="text-sm text-gray-600 mb-4">
            Add any qualitative observations from site visits or management interviews
          </p>

          <textarea
            name="credit_officer_notes"
            value={formData.credit_officer_notes}
            onChange={handleInputChange}
            rows={4}
            placeholder="e.g., Factory visited on Tuesday. Operations look solid, but machinery is aging and operating at 60% capacity."
            className="input-field resize-none"
          />
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary flex items-center space-x-2"
            disabled={loading}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Processing...</span>
              </>
            ) : (
              <>
                <FileText size={20} />
                <span>Generate Credit Appraisal</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

const FileUploadField = ({ label, accept, file, onChange }) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-blue-500 transition-colors">
        <input
          type="file"
          accept={accept}
          onChange={onChange}
          className="hidden"
          id={label}
        />
        <label
          htmlFor={label}
          className="flex items-center justify-center cursor-pointer"
        >
          {file ? (
            <div className="flex items-center space-x-2 text-green-600">
              <FileText size={20} />
              <span className="font-medium">{file.name}</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-gray-500">
              <Upload size={20} />
              <span>Click to upload or drag and drop</span>
            </div>
          )}
        </label>
      </div>
    </div>
  );
};

export default NewApplication;
