import { useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom"; // added to the existing import
import { useAuthStore } from "@/features/auth/store";
import { publicRequest } from "@/lib/api-client";

//link: react router components that lets user navigate to another route without reloading the entire page by updating url and render the appropriate rreact components
//outlet: react router components that act as a placeholder where the currently matched child route's component is rendered inside a fixed parent layout (usually holds the components that frquently changes on every url change)

const AdminLayout = () => {
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      //publicRequest, not apiRequest: logout only needs the cookie. apiRequest also checks the access, which we dont need that. 
      await publicRequest("/api/auth/logout", { method: "POST" });
    } catch {
      //even if the worst case: server side failed (jti in redis is not deleted), the local session must still end. Continue to finally
    } finally {
      clearAuth(); //ProtectedRoute sees no token and redirects
      navigate("/admin/login", { replace: true }); //"replace: true" as a second argument: react router dom will internally swap the link instead of adding new one
    }
  };

  return (
    <div className="flex h-screen"> {/*horizontally*/}

      {/*the sidebar: which stays mounted (it is created once and remains rendered) across all pages */}
      <aside className="flex flex-col w-64 bg-gray-100 p-4">  {/*aside: semantic html name for div meaning side content (used for readability)*/}
        <h2 className="text-lg font-bold mb-6">Klinik Admin</h2>

        {/*nav: semantic html name for div meaning contains hypertext reference*/}
        <nav className="flex flex-col gap-2">
          <Link to="/admin/bookings" className="hover:underline">
            Bookings
          </Link>
          <Link to="/admin/stats" className="hover:underline">
            Stats
          </Link>
        </nav>
        {/*Shows the email, role, and logout button*/}
        <div className="mt-auto space-y-2 border-t border-gray-300 pt-4">
          {user && (
            <div className="text-xs text-gray-500">
              <p className="truncate font-medium text-gray-700">{user.email}</p>
              <p>{user.role}</p>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
          >
            {isLoggingOut ? "Logging out..." : "Log out"}
          </button>
        </div>
      </aside>

      {/*main content: this is what being rerendered based on the matched child route*/}
      <main className="flex-1 p-6 overflow-y-auto">
        <Outlet /> {/*AdminLayout renders unconditionally whenever the url starts with "/admin", and outlet is the reserved spot where whichever child matched gets rendered in.*/}
      </main>
    </div>
  );
};

export default AdminLayout;