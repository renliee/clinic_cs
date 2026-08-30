//Note: Refresh token is sent using httpOnly cookie as credentials, while access token is sent using Bearer header
import { useAuthStore } from "@/features/auth/store";

//define a custom error that has its on detail info (status code and explanation string)
export class ApiError extends Error { 
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail); //super(detail) runs the parent class's (Error) own constructor with detail, so the parent's part of the object gets built correctly, before the child adds its own extra pieces (status).
    this.status = status;
    this.detail = detail;
  }
}

//prepare the full url for every API call 
function buildUrl(path: string): string {
  return `${import.meta.env.VITE_API_URL}${path}`;
}

//receive Response object from backend and check on it (if it works = give the data, if it fails = throw a proper error)
async function parseResponse(response: Response) {
  if (response.status === 204) { //if success but null body
    return null;
  }

  //parse the body first to get the information first
  let data;
  try {
    data = await response.json(); //take the JSON body from response object to a dict that JS understand
  } catch {
    throw new ApiError(response.status, response.statusText || "Something went wrong");
  }

  if (!response.ok) { //if it isnt around 200-299
    const detail = typeof data.detail === "string" ? data.detail : "Something went wrong"; //if data.detail is a string = use it, otherwise = use the fallback
    throw new ApiError(response.status, detail);
  }

  return data; 
}

//used for /api/auth/login and /api/auth/refresh (2 endpoints where token is not necessary) 
export async function publicRequest(path: string, options: RequestInit = {}) { //RequestInit: TS build-in for the second args that will normally be passed to fetch (method, body, etc). {} as default if null
  //send the body and header to backend to be checked
  const response = await fetch(buildUrl(path), {
    ...options, //copy every key:value pairs from options to this dict (merge it with credentials and header)
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include", //allow httpOnly cookies alongside the system
  }); 
 
  return parseResponse(response); //check the response from backend, is it a success status code or not
}

//function to get a fresh access token (acc token dies every 15 min) using the refresh cookie the borwser has
async function doRefresh(): Promise<string> {
  try {
    const data = await publicRequest("/api/auth/refresh", { method: "POST" }); //sent request to endpoint that refresh the access token, using refresh token stored at redis 
    useAuthStore.getState().setAccessToken(data.access_token); //set the new access token to zustand store
    return data.access_token;
  } catch (err) {
    useAuthStore.getState().clearAuth(); //clear the user auth if refreshing failed
    throw err;
  }
}

//set it null initially 
let refreshPromise: Promise<string> | null = null;

//call this function if refreshing access token is needed (every 15 min)
export function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise; //if there is still a refresh process going on, return that promise object (will return the same access token later when done)
  refreshPromise = doRefresh().finally(() => { //do the refresh (while awaiting, the value of refreshPromise is promise object, not null), finally set the value to null again.
    refreshPromise = null;
  });
  return refreshPromise; //return the promise (bcs return is not waiting for finally block to be done)
}

//Used by app to send request to backend. If the token turns out to be dead, this function quietly try to fix that (refresh it)
export async function apiRequest<T = any>(
  path: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> {
  const token = useAuthStore.getState().accessToken;

  const response = await fetch(buildUrl(path), {
    ...options, //copy every key:value from options to this dict
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}), //if there is token, add Authorization header as extra info
      ...options.headers,
    },
    credentials: "include", //Allow httpOnly cookie alongside the system
  });

  //if req isnt failed, do parseResponse (401 is a value where the token died, expired, or anything that may be fix using the refresh method)
  if (response.status !== 401) {
    return parseResponse(response);
  }

  //if status is 401, check: have i tried to refresh?
  if (isRetry) {
    useAuthStore.getState().clearAuth();
    throw new ApiError(401, "Session expired");
  }

  //if refresh has not done, do it and call the function once more with new isRetry value
  await refreshAccessToken();
  return apiRequest<T>(path, options, true);
}