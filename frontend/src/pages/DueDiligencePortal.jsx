import { useParams } from 'react-router-dom';

const DueDiligencePortal = () => {
  const { id } = useParams();

  return (
    <div className="card">
      <h1 className="text-2xl font-bold mb-4">Due Diligence Portal</h1>
      <p className="text-gray-600">Add and manage due diligence notes for application {id}</p>
      <p className="text-sm text-gray-500 mt-2">Coming soon...</p>
    </div>
  );
};

export default DueDiligencePortal;
