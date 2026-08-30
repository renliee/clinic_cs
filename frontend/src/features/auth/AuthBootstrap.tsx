import { useEffect, Suspense } from "react";
import { Outlet } from "react-router-dom";
import { useAuthStore } from "@/features/auth/store";
import { apiRequest, refreshAccessToken } from "@/lib/api-client";
import type { User } from "@/features/auth/types";

let bootstrapStarted = false; //variable to assure the refresh only happen once

const AuthBootstrap = () => {
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping); //act as the var to show is it still processing or not (initial value = true)

  useEffect(() => {
    if (bootstrapStarted) return; //already attempted this page load, don't repeat
    bootstrapStarted = true;

    //most important part, to try refresh the access token after a reset from JS memory (can be hard refresh, new tab, etc)
    const restoreSession = async () => {
      const { setAuth, setBootstrapped } = useAuthStore.getState(); //get the setAuth and setBootstrapped var from all the variable at useAuthStore
      try {
        //the httpOnly cookie decides: valid = new access token, expired = throws
        const token = await refreshAccessToken();
        const user = await apiRequest<User>("/api/auth/me");
        setAuth(token, user);
      } catch {
        //On failure, the store just quietly stays in its already logged out starting state, and the only thing that changes is isBootstrapping flipping to false, which is what finally lets ProtectedRoute make its "not logged in" decision (through return "Outlet" below).
      } finally {
        setBootstrapped(); //set isBootstrapping to false (shows that the check is done and no need to show "Loading..." again)
      }
    };

    restoreSession();
  }, []); //[] meaning only run once, bcs there is no value in it which wont trigger a value to change (react always rerun if there is a value changed inside array)

  //if the bootstrapped is still on process (isBootstrapping = true) then show Loading text, if = false then ignore
  if (isBootstrapping) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-gray-500">
        Loading...
      </div>
    );
  }

  //Lazy loaded pages (AdminLayout, BookingPage, etc) are downloaded when needed. While we are waiting the download, we show the fallback "Loading..." below  
  //Outlet: return the child page after the bootstrap process
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-sm text-gray-500">Loading...</div>}>
      <Outlet /> 
    </Suspense>
  );
};

export default AuthBootstrap;