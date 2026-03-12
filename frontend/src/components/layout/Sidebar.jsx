import {
    FileText,
    LayoutDashboard,
    Shield,
    X
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useUIStore } from '../../store/uiStore';

const Sidebar = () => {
  const location = useLocation();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/new-application', icon: FileText, label: 'New Application' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-charcoal text-white w-64 transform transition-transform duration-200 ease-in-out z-30 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-sienna to-terracotta rounded-full flex items-center justify-center shadow-lg">
                <Shield size={18} color="#FAF7F2" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-terracotta leading-none mb-1">Corporate Intelligence</p>
                <h1 className="font-serif text-xl font-bold leading-none tracking-tight">FinIntel</h1>
              </div>
            </div>
            <button
              onClick={toggleSidebar}
              className="lg:hidden text-white"
            >
              <X size={24} />
            </button>
          </div>

          <nav>
            <ul className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                        isActive(item.path)
                          ? 'bg-sienna text-white'
                          : 'text-warm-border hover:bg-ink'
                      }`}
                    >
                      <Icon size={20} />
                      <span className="font-sans text-sm">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>


      </aside>
    </>
  );
};

export default Sidebar;
