"use client";
import { useCallback, useEffect, useState } from "react";
import { api, type Status } from "./api";

/** Shared investigation state. Auto-starts the agents on first visit so pages are never empty. */
export function useStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try { setStatus(await api.status(true)); setError(null); } catch (e) { setError(String(e)); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  const restart = async () => { setBusy(true); try { await api.start(); await refresh(); } catch (e) { setError(String(e)); } finally { setBusy(false); } };
  const answer = async (id: string, value: string) => { setBusy(true); try { await api.answer(id, value); await refresh(); } catch (e) { setError(String(e)); } finally { setBusy(false); } };
  const decide = async (id: string, decision: string) => { setBusy(true); try { await api.decide(id, decision); await refresh(); } finally { setBusy(false); } };

  return { status, busy, error, refresh, restart, answer, decide };
}
