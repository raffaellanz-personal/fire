import "../App.css";
import { NavLink } from "react-router-dom";
import {
  AlertTriangle,
  BookOpen,
  FileText,
  Home,
  Mail,
  MessageSquare,
  Shield,
  Timeline,
} from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/timeline", label: "Timeline", icon: Timeline },
  { to: "/emails", label: "Emails", icon: Mail },
  { to: "/threads", label: "Threads", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/issues", label: "Issues", icon: AlertTriangle },
  { to: "/laws", label: "Laws & Policies", icon: BookOpen },
  { to: "/strategy", label: "Strategy", icon: Shield },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebarHeader">
        <h2>Fire Claim Review</h2>
        <p>23 Mays Street, Devonport</p>
      </div>

      <nav className="sidebarNav">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              isActive ? "navLink activeNavLink" : "navLink"
            }
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
