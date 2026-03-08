import { Bell, Menu } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

const Header = () => {
  const { toggleSidebar } = useUIStore();

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
      <button
        onClick={toggleSidebar}
        className="lg:hidden text-gray-600 hover:text-gray-900"
      >
        <Menu size={24} />
      </button>

      <div className="flex-1 lg:hidden" />

      <div className="flex items-center space-x-4">
        <button className="relative text-gray-600 hover:text-gray-900">
          <Bell size={20} />
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
            3
          </span>
        </button>
      </div>
    </header>
  );
};

export default Header;
