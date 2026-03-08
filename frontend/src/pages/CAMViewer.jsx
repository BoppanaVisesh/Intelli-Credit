import { useParams } from 'react-router-dom';

const CAMViewer = () => {
  const { id } = useParams();

  return (
    <div className="card">
      <h1 className="text-2xl font-bold mb-4">CAM Viewer</h1>
      <p className="text-gray-600">Credit Appraisal Memo viewer for application {id}</p>
      <p className="text-sm text-gray-500 mt-2">Coming soon...</p>
    </div>
  );
};

export default CAMViewer;
