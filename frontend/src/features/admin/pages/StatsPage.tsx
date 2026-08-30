/* STATS FLOW
This page will GET /api/admin/stats every 30s, so a booking made elsewhere (customer via chat, or another admin) 
shows up here within 30s at worst. Navigating to this page fetches GET immediately, so that delay only applies 
to a tab left sitting open.

Backend side: the endpoint answers from a Redis note instead of running 4 SQL queries every time. 
Any booking change (from admin/user) deletes that note, so the next request will call new info from Postgres. 
The note also self deletes after 30s as a fallback. Then notes will be refill if there is a request coming from browser. 
The two 30s are unrelated: one is browser timer to do fetch, one is the redis note's lifespan. */

import { useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api-client";
import type { Stats } from "@/features/admin/types";

//matches the backend cache TTL: polling faster than this just re-reads the same cached value
const REFRESH_MS = 30_000;

const CARDS: { key: keyof Stats; label: string; hint: string }[] = [
  { key: "today_bookings", label: "Today", hint: "Bookings scheduled for today" },
  { key: "this_week_total", label: "This week", hint: "Bookings in the current week" },
  { key: "pending_count", label: "Pending", hint: "Waiting for confirmation" },
  { key: "confirmed_count", label: "Confirmed", hint: "Confirmed, not yet completed" },
];

const StatsPage = () => {
  const [stats, setStats] = useState<Stats | null>(null); //hold the stats information
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null); //text shown at frontend to tell when the numbers were last confirmed fresh

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await apiRequest<Stats>("/api/admin/stats");
        if (cancelled) return;
        setStats(data);
        setUpdatedAt(new Date());
        setError(null); //clears a previous failure
      } catch (err) {
        if (cancelled) return;
        //keep the last good numbers on screen, just flag that they're stale
        setError(err instanceof ApiError ? err.detail : "Failed to load stats");
      }
    };

    //setInterval runs function automatically every miliseconds of inputted value (in this case, runs "load" every 30 secs)
    load(); //needed, act as the initializer at build up, continued by setInterval afterwards
    const timer = setInterval(load, REFRESH_MS);

    //cleanup function below will execute only if the value inside the array change OR unmount happens. 
    return () => {
      cancelled = true; //will ignore the response from stale apiRequest 
      clearInterval(timer); //stops the interval calling permanently. Without this, every remount would leave another timer running forever (multi running interval)
    };
  }, []);

  return (
    <div className="space-y-4">
      {/*Header (Stats and updatedAt*/}
      <div className="flex items-baseline justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Stats</h1>
        {updatedAt && (
          <span className="text-xs text-gray-400">
            Updated {updatedAt.toLocaleTimeString("id-ID")}
          </span>
        )}
      </div>
      
      {/*Shows error*/}
      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {/*Show the booking stats*/}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {CARDS.map((card) => (
          <div key={card.key} className="rounded-xl border border-gray-200 bg-white p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{card.label}</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {stats ? stats[card.key] : "—"}
            </p>
            <p className="mt-1 text-xs text-gray-400">{card.hint}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatsPage;