import { useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api-client";
import type { Booking, BookingListResponse, BookingStatus } from "@/features/admin/types";

const STATUS_FILTERS = ["ALL", "PENDING", "CONFIRMED", "CANCELED", "COMPLETED"] as const; //make this list of array readonly 
type StatusFilter = (typeof STATUS_FILTERS)[number]; //StatusFilter = type of that array and index to that type using any number, will be "ALL" | "PENDING" | "CONFIRMED" 

//note: record is a type for key:value pairs
const STATUS_STYLES: Record<BookingStatus, string> = {
  PENDING: "bg-amber-100 text-amber-800",
  CONFIRMED: "bg-teal-100 text-teal-800",
  CANCELED: "bg-red-100 text-red-700",
  COMPLETED: "bg-gray-200 text-gray-700",
};

//which transitions make sense from the row's current status
const NEXT_ACTIONS: Record<BookingStatus, BookingStatus[]> = {
  PENDING: ["CONFIRMED", "CANCELED"],
  CONFIRMED: ["COMPLETED", "CANCELED"],
  CANCELED: [],
  COMPLETED: [],
};

const ACTION_LABELS: Record<BookingStatus, string> = {
  PENDING: "Pending",
  CONFIRMED: "Confirm",
  CANCELED: "Cancel",
  COMPLETED: "Complete",
};

//format the date from backend to a readable string
const formatDate = (isoDate: string): string => {
  const parsed = new Date(isoDate); //parse the string date from backend to object date that the system understand
  if (Number.isNaN(parsed.getTime())) return isoDate; //check "parsed", is it a valid date object? or NaN (not a number). 
  return parsed.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" }); //format the date object to a readable string by user (id-ID: local code for indo's time). 
};

const BookingsPage = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [filter, setFilter] = useState<StatusFilter>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0); //as a constant to do refresh on useEffect filter, without changing the filter
  
  useEffect(() => {
    //cancelled matters: Action A send filter req, user changed mind and do diff filter req. That second dropdown click changes filter right away, that's what flips A's cancelled to true, way before A's response ever comes back; A's response arriving late just gets checked against a flag that was already flipped.
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const query = filter === "ALL" ? "" : `?status=${filter}`; //FastAPI will recognize ?status as params for the endpoints bcs it match {} at the backend url. (check api/routes/bookings.py)
        const data = await apiRequest<BookingListResponse>(`/api/admin/bookings${query}`);
        if (!cancelled) setBookings(data.bookings);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load bookings");
        }
      } finally {
        if (!cancelled) setIsLoading(false); //to tell that loading is done and will render the UI 
      }
    };

    load();
    return () => { cancelled = true;};  //this wont be run directly, only executed if [filter, reloadKey] change OR the page unmount. 
  }, [filter, reloadKey]); //if reload key or filter changed, the useEffect will run again

  //runs when confirm/cancel/complete button is clicked, tell the backend to update that status and make the screen/UI updated
  const handleStatusChange = async (bookingId: string, status: BookingStatus) => {
    setUpdatingId(bookingId);
    setError(null);
    try {
      await apiRequest(`/api/admin/bookings/${bookingId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setReloadKey((k) => k + 1); //update reloadkey, so react re-render and refetch the booking list (removing rows that no longer match the new status filter)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to update booking");
    } finally {
      setUpdatingId(null);  
    }
  };

  return (
    <div className="space-y-4">
      {/*The header and select status dropdown*/}
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Bookings</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as StatusFilter)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-teal-600"
        >
          {STATUS_FILTERS.map((option) => (
            <option key={option} value={option}>
              {option === "ALL" ? "All statuses" : option}
            </option>
          ))}
        </select>
      </div>
      
      {/*Show some error if there exist*/}
      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {/*JSX return one of these 3 branch of ternary operator below : 
      - If isLoading true = shows Loading text. 
      - If isLoading false and no bookings yet = shows text that inform empty bookings. 
      - If isLoading false and there is bookings = show them*/}
      
      {isLoading && bookings.length === 0 ? (
        <p className="text-sm text-gray-500">Loading bookings...</p>
      ) : bookings.length === 0 ? (
        <p className="text-sm text-gray-500">
          {filter === "ALL" ? "No bookings yet." : `No ${filter.toLowerCase()} bookings.`}
        </p>
      ) : (
        <div className={`overflow-x-auto rounded-xl border border-gray-200 bg-white transition-opacity ${isLoading ? "opacity-50 pointer-events-none" : ""}`}> {/*if fetching status is in process, make the table opacity to 50 and entire tables become unclickable*/}
          <table className="w-full text-left text-sm">
            {/*Table head*/}
            <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3 font-medium">Booking</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Treatment</th>
                <th className="px-4 py-3 font-medium">Schedule</th>
                <th className="px-4 py-3 font-medium">Branch</th> 
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            {/*At the table body, divide-y to make line threshold between rows*/}
            <tbody className="divide-y divide-gray-100">
              {bookings.map((booking) => {
                const isUpdating = updatingId === booking.booking_id;
                return (
                  <tr key={booking.booking_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{booking.booking_id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{booking.nama}</td>
                    <td className="px-4 py-3 text-gray-700">{booking.treatment}</td>
                    <td className="px-4 py-3 text-gray-700">{formatDate(booking.tanggal)} - {booking.jam}</td>
                    <td className="px-4 py-3 text-gray-700">{booking.lokasi}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLES[booking.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {booking.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {/*for unknown status: Render nothing as the system dont know how to handle the next action buttons (avoid crash)*/}
                        {(NEXT_ACTIONS[booking.status] ?? []).map((next) => (
                          <button
                            key={next}
                            type="button"
                            disabled={isUpdating}
                            onClick={() => handleStatusChange(booking.booking_id, next)}
                            className={`rounded-md px-2.5 py-1 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50 ${
                              next === "CANCELED"
                                ? "bg-red-50 text-red-700 hover:bg-red-100"
                                : "bg-teal-600 text-white hover:bg-teal-700"
                            }`}
                          >
                            {isUpdating ? "..." : ACTION_LABELS[next]}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default BookingsPage;