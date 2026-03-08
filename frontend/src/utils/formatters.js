export const formatCurrency = (value, currency = '₹', crores = true) => {
  if (value === null || value === undefined) return 'N/A';
  
  if (crores) {
    return `${currency}${value.toFixed(2)} Cr`;
  }
  
  return `${currency}${value.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export const formatPercentage = (value, decimals = 2) => {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(decimals)}%`;
};

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const getScoreColor = (score) => {
  if (score >= 75) return 'text-green-600';
  if (score >= 50) return 'text-yellow-600';
  return 'text-red-600';
};

export const getDecisionBadgeClass = (decision) => {
  switch (decision) {
    case 'APPROVE':
      return 'bg-green-100 text-green-800';
    case 'CONDITIONAL_APPROVE':
      return 'bg-yellow-100 text-yellow-800';
    case 'REJECT':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const getRiskLevelClass = (level) => {
  switch (level) {
    case 'LOW':
      return 'text-green-600';
    case 'MEDIUM':
      return 'text-yellow-600';
    case 'HIGH':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};
