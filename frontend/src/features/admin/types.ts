//mirrors the backend response from models/schemas.py (Booking and BookingListResponse)
export type BookingStatus = "PENDING" | "CONFIRMED" | "CANCELED" | "COMPLETED";

export interface Booking {
  booking_id: string;
  user_id: string;
  nama: string;
  lokasi: string;
  treatment: string;
  tanggal: string; //"2026-08-29"
  jam: string; //"14:30"
  status: BookingStatus;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
  confirmed_at: string | null;
}

//mirrors BookingListResponse
export interface BookingListResponse {
  bookings: Booking[];
  total: number;
}

//mirrors StatsResponse
export interface Stats {
  today_bookings: number;
  this_week_total: number;
  pending_count: number;
  confirmed_count: number;
}