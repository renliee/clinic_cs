import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, Navigate} from "react-router-dom";
import { useAuthStore } from "@/features/auth/store";
import { publicRequest, apiRequest, ApiError } from "@/lib/api-client";
import type { User } from "@/features/auth/types";

//shape of POST /api/auth/login response (backend TokenResponse)    
interface LoginResponse {
  access_token: string; //used to access future authorization request
  token_type: string;
  expires_in: number;
}

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const navigate = useNavigate();//prepare the navigate object 
  //selector form: component only re-renders if the picked action changes (it never does)
  const setAuth = useAuthStore((s) => s.setAuth);
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const accessToken = useAuthStore((s) => s.accessToken);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); //stop the browser's default full page reload on submitted form 
    setError(null); //clear the previous attempt's message
    setIsSubmitting(true); 

    try {
      //1. exchange credentials for an access token (refresh token arrives as httpOnly cookie)
      const data: LoginResponse = await publicRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      //2. token must be in the store BEFORE /me, apiRequest reads it from there
      setAccessToken(data.access_token);

      //3. login response carries no user info, fetch it separately
      const user = await apiRequest<User>("/api/auth/me");

      //4. now both fields are filled
      setAuth(data.access_token, user);

      //5. navigate to the /admin/bookings url, while keeping the side tab; "replace: true" so the back button doesn't return to login and create infinite loops
      navigate("/admin/bookings", { replace: true }); 
    } catch (err) {
      clearAuth(); //never leave a half filled store (token set, user null)
      //true only if backend responded (not a network failure) AND rejected the login specifically (401)
      if (err instanceof ApiError && err.status === 401) {
        setError(err.detail); //backend sends a generic "Invalid email or password"
      } else {
        //only if the error is not from bad authentication
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  //Important: if there is a valid access token at the store, directly redirect the page to /admin/bookings (login page wont be shown)
  if (accessToken) return <Navigate to="/admin/bookings" replace />;

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-sm space-y-5"
      >
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-gray-900">Klinik Admin</h1>
          <p className="text-sm text-gray-500">Sign in to manage bookings</p>
        </div>

        <div className="space-y-2">
            {/*htmlFor is used to link the header "Email" to the email input, helped by the id at the <input>*/}
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          {/*type give a warning if the input is not in general based on what type the input is*/}
          <input
            id="email"
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            disabled={isSubmitting}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-1 focus:ring-teal-600 disabled:bg-gray-100"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            disabled={isSubmitting}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-600 focus:ring-1 focus:ring-teal-600 disabled:bg-gray-100"
          />
        </div>

        {/*div below is an alert and will directly show the text if error happened*/}
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}

        {/*Text inside the button will change based on the state of "isSubmitting"*/}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;