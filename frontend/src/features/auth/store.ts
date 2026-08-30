import { create } from "zustand"; //create: used to make a store of info, often paired with "set" which task is to change the store's value. 
import type { User } from "@/features/auth/types";

//type checker for our useAuthStore
interface AuthState {
  accessToken: string | null;
  user: User | null;
  isBootstrapping: boolean;
  setAuth: (accessToken: string, user: User) => void; //setAuth: variable that its type is a function that has 2 params (accessToken and user) then returns nothing
  setAccessToken: (accessToken: string) => void;
  clearAuth: () => void; //clearAuth: variable that its type is a function that has no params and returns nothing
  setBootstrapped: () => void;
}

//making the store using create, set act as params bcs it will be used inside. (set is special function from zustand to change value)
export const useAuthStore = create<AuthState>((set) => ({
  //initial value
  accessToken: null,
  user: null,
  isBootstrapping: true,
  //function to change the store's value (notes: set returns void -> from the documentation)
  //setAuth: a function with accessToken and user as its params, which will change the value of accessToken and user in the store based on what is given at the params
  setAuth: (accessToken, user) => set({ accessToken, user }), //used after a successful login 
  setAccessToken: (accessToken) => set({ accessToken }), //used after a refresh of access token 
  clearAuth: () => set({ accessToken: null, user: null }), //clearAuth: function that clears the store's values which is accessToken and user (logout/refresh fails)
  setBootstrapped: () => set({ isBootstrapping: false }), //used once when the app starts (checking, is this person actually still logged in?)
}));