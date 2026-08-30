export interface User {
    id: string;
    email: string;
    role: "ADMIN" | "STAFF" | "VIEWER";
    is_active: boolean;
    created_at: string;
    last_login_at: string | null;
}


