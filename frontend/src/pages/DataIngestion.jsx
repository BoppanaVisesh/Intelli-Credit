import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { uploadDocuments, parseDocuments, getDocuments } from '../utils/api';

const DataIngestion = () => {
  const { id } = useParams();
  
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Fetch existing documents on load
  useEffect(() => {
    if (id) {
      fetchDocuments();
    }
  }, [id]);

  const fetchDocuments = async () => {
    try {
      const response = await getDocuments(id);
      setUploadedDocs(response.documents || []);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (fileList) => {
    const newFiles = Array.from(fileList).map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type
    }));
    setFiles(prev => [...prev, ...newFiles]);
    setError(null);
  };

  const removeFile = (fileId) => {
    setFiles(files.filter(f => f.id !== fileId));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select files to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const formData = new FormData();
      formData.append('application_id', id);
      
      files.forEach(({ file }) => {
        formData.append('files', file);
      });

      const response = await uploadDocuments(formData);
      
      setSuccessMessage(`Successfully uploaded ${response.total_files} file(s)`);
      setFiles([]);
      
      // Fetch updated documents list
      await fetchDocuments();
      
    } catch (err) {
      setError(err.message || 'Failed to upload files');
    } finally {
      setUploading(false);
    }
  };

  const handleParse = async () => {
    setParsing(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await parseDocuments(id);
      
      if (response.parsed_count > 0) {
        setSuccessMessage(`Successfully parsed ${response.parsed_count} document(s)`);
      } else {
        setSuccessMessage(response.message || 'No pending documents to parse');
      }
      
      // Fetch updated documents list
      await fetchDocuments();
      
    } catch (err) {
      setError(err.message || 'Failed to parse documents');
    } finally {
      setParsing(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getDocTypeIcon = (type) => {
    const icons = {
      'BANK_STATEMENT': '🏦',
      'GST_RETURN': '📊',
      'ITR': '📄',
      'ANNUAL_REPORT': '📈',
      'BALANCE_SHEET': '💰',
      'OTHER': '📎'
    };
    return icons[type] || '📎';
  };

  const getStatusBadge = (status) => {
    const styles = {
      'PENDING': 'bg-yellow-100 text-yellow-800',
      'IN_PROGRESS': 'bg-blue-100 text-blue-800',
      'COMPLETED': 'bg-green-100 text-green-800',
      'FAILED': 'bg-red-100 text-red-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-2xl font-bold mb-2">Document Upload & Parsing</h1>
        <p className="text-gray-600 mb-6">Application ID: {id}</p>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        
        {successMessage && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-800">{successMessage}</p>
          </div>
        )}

        {/* Drag & Drop Upload Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <div className="space-y-4">
            <div className="text-4xl">📁</div>
            <div>
              <p className="text-lg font-medium text-gray-700">
                Drag & drop files here
              </p>
              <p className="text-sm text-gray-500 mt-1">
                or click to browse
              </p>
            </div>
            <input
              type="file"
              multiple
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
              accept=".pdf,.xlsx,.xls,.csv"
            />
            <label
              htmlFor="file-upload"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer transition-colors"
            >
              Select Files
            </label>
            <p className="text-xs text-gray-500">
              Supported: PDF, Excel (.xlsx, .xls), CSV
            </p>
          </div>
        </div>

        {/* Selected Files List */}
        {files.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3">Selected Files ({files.length})</h3>
            <div className="space-y-2">
              {files.map(({ id, name, size }) => (
                <div key={id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">📄</span>
                    <div>
                      <p className="font-medium text-gray-900">{name}</p>
                      <p className="text-sm text-gray-500">{formatFileSize(size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(id)}
                    className="text-red-600 hover:text-red-800 font-medium"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
            
            <div className="mt-4 flex space-x-3">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? 'Uploading...' : `Upload ${files.length} File(s)`}
              </button>
              <button
                onClick={() => setFiles([])}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Uploaded Documents */}
      {uploadedDocs.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Uploaded Documents ({uploadedDocs.length})</h2>
            <button
              onClick={handleParse}
              disabled={parsing}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {parsing ? 'Parsing...' : 'Parse Pending Documents'}
            </button>
          </div>

          <div className="space-y-3">
            {uploadedDocs.map((doc) => (
              <div key={doc.file_id} className="border rounded-lg p-4 hover:border-blue-300 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <span className="text-3xl">{getDocTypeIcon(doc.document_type)}</span>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="font-semibold text-gray-900">{doc.filename}</h3>
                        {getStatusBadge(doc.parse_status)}
                      </div>
                      
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>Type: <span className="font-medium">{doc.document_type.replace('_', ' ')}</span></p>
                        <p>Classification Confidence: <span className="font-medium">{(doc.classification_confidence * 100).toFixed(0)}%</span></p>
                        {doc.uploaded_at && (
                          <p>Uploaded: {new Date(doc.uploaded_at).toLocaleString()}</p>
                        )}
                        {doc.parsed_at && (
                          <p>Parsed: {new Date(doc.parsed_at).toLocaleString()}</p>
                        )}
                      </div>

                      {/* Parsed Data Preview */}
                      {doc.parse_status === 'COMPLETED' && doc.parsed_data && (
                        <details className="mt-3">
                          <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium">
                            View Extracted Data
                          </summary>
                          <div className="mt-2 p-3 bg-gray-50 rounded-md">
                            <pre className="text-xs overflow-auto max-h-64">
                              {JSON.stringify(doc.parsed_data, null, 2)}
                            </pre>
                          </div>
                        </details>
                      )}

                      {/* Error Message */}
                      {doc.parse_status === 'FAILED' && doc.parse_error && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                          <strong>Error:</strong> {doc.parse_error}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {uploadedDocs.length === 0 && files.length === 0 && (
        <div className="card text-center py-12">
          <div className="text-6xl mb-4">📤</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No Documents Uploaded</h3>
          <p className="text-gray-500">Upload your first document to get started</p>
        </div>
      )}
    </div>
  );
};

export default DataIngestion;
