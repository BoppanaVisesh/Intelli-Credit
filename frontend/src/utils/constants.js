export const DECISION_LABELS = {
  APPROVE: 'Approved',
  CONDITIONAL_APPROVE: 'Conditional Approval',
  REJECT: 'Rejected',
};

export const RISK_LEVELS = {
  LOW: 'Low Risk',
  MEDIUM: 'Medium Risk',
  HIGH: 'High Risk',
};

export const APPLICATION_STATUS = {
  PENDING: 'Pending',
  PROCESSING: 'Processing',
  COMPLETED: 'Completed',
  REJECTED: 'Rejected',
};

export const FIVE_CS = [
  {
    id: 'character',
    label: 'Character',
    description: 'Promoter background, litigation, reputation',
    icon: '👤',
  },
  {
    id: 'capacity',
    label: 'Capacity',
    description: 'Ability to repay from cash flows',
    icon: '💪',
  },
  {
    id: 'capital',
    label: 'Capital',
    description: 'Financial strength and equity base',
    icon: '💰',
  },
  {
    id: 'collateral',
    label: 'Collateral',
    description: 'Assets available for security',
    icon: '🏢',
  },
  {
    id: 'conditions',
    label: 'Conditions',
    description: 'Market and sector conditions',
    icon: '🌐',
  },
];
