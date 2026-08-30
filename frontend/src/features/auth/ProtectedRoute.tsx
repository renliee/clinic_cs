import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/features/auth/store";

const ProtectedRoute = () => {
  const accessToken = useAuthStore((s) => s.accessToken); //get the acces token value from the store
  if (!accessToken) return <Navigate to="/admin/login" replace />; //no access token (invalid), navigate to the login page
  return <Outlet />; //access token is there, let the supposed page render here
};

export default ProtectedRoute;