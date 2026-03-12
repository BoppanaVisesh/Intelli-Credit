import { Menu } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';

const Header = () => {
  const { toggleSidebar } = useUIStore();

  return (
    <header className="bg-warm-white border-b border-warm-border h-16 flex items-center justify-between px-6">
      <button
        onClick={toggleSidebar}
        className="lg:hidden text-muted hover:text-charcoal"
      >
        <Menu size={24} />
      </button>

      <div className="flex-1 lg:hidden" />

      <div className="flex items-center space-x-4">
        <span className="hidden lg:block font-mono text-xs text-muted tracking-wider">
          {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </span>
      </div>
    </header>
  );
};

export default Header;
