/* AUTH FLOW SUMMARY
Access token lives only in JS memory (Zustand) and always wiped on every reload/hard refresh.
Refresh token lives in an httpOnly cookie which survives reload, invisible to JS.

On app startup, AuthBootstrap tries to trade that cookie for a fresh access token + user, 
and blocks rendering (shows "Loading...") until that check finishes. Then let <Outlet> show the child page.
ProtectedRoute runs after AuthBootstrap is done. It only checks what's in the store: 
token present = render the real page; token missing = redirect to /admin/login.

Nesting order matters, AuthBootstrap must wrap ProtectedRoute, so the cookie check always finishes before 
the login/no-login decision is made. Without AuthBootstrap, every hard refresh inside ProtectedRoute would 
look identical to "never logged in", even with a perfectly valid refresh cookie sitting in the browser.*/

import { lazy, Suspense } from "react"; //lazy: function that delays downloading a component's code until the moment it's actually about to be rendered; Suspense: shows a fallback while that code loads
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"; //BrowserRouter watch browser's current URL bar and makes current path available for Routes
import AuthBootstrap from "@/features/auth/AuthBootstrap"; //not lazy: it must run on every admin page load
import ProtectedRoute from "@/features/auth/ProtectedRoute";

//why lazy is used: chat customers and admin dashboard users never need each other's code, so lazy splits them into separate chunks
const ChatWindow = lazy(() => import("@/features/chat/components/ChatWindow"));
const AdminLayout = lazy(() => import("@/features/admin/components/AdminLayout"));
const LoginPage = lazy(() => import("@/features/admin/pages/LoginPage"));
const BookingsPage = lazy(() => import("@/features/admin/pages/BookingsPage"));
const BookingDetailPage = lazy(() => import("@/features/admin/pages/BookingDetailPage"));
const StatsPage = lazy(() => import("@/features/admin/pages/StatsPage"));

const App = () => {
    return (
        <BrowserRouter>
            <Suspense fallback={<div>Loading...</div>}>
                <Routes>
                    {/*If the curr url matches with the route path, element inside it will be executed*/}
                    <Route path="/" element={<ChatWindow />} /> {/*outside AuthBootstrap: anonymous customers never trigger a refresh call*/}

                    {/*Runs the silent session restore before any admin page renders*/}
                    <Route element={<AuthBootstrap />}>
                        <Route path="/admin/login" element={<LoginPage />} /> {/*inside bootstrap (so a valid cookie can skip the form) but outside ProtectedRoute (no token needed to see it)*/}

                        {/*Protected endpoints: no token in store means redirect to /admin/login*/}
                        <Route element={<ProtectedRoute />}>
                            <Route path="/admin" element={<AdminLayout />}>
                                {/*index means: if path is "/admin" only, run the elements. Which navigate will change the curr url by adding /bookings*/}
                                <Route index element={<Navigate to="bookings" replace />} /> {/*replace: replace curr url ("/admin") to "/admin/bookings", so that when user presses back, it wont bounce*/}
                                <Route path="bookings" element={<BookingsPage />} />
                                <Route path="bookings/:id" element={<BookingDetailPage />} /> {/*:id is a placeholder that matches any value in that position*/}
                                <Route path="stats" element={<StatsPage />} />
                            </Route>
                        </Route>
                    </Route>
                </Routes>
            </Suspense>
        </BrowserRouter>
    );
};

export default App;