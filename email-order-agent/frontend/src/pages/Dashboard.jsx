import { useEffect, useState } from "react";
import { api } from "../api";

export default function Dashboard() {
  const [enabled, setEnabled] = useState(false);

  async function load() {
    const res = await api.get("/agent/status");
    setEnabled(res.data.enabled);
  }

  async function start() {
    await api.post("/agent/start");
    await load();
  }

  async function stop() {
    await api.post("/agent/stop");
    await load();
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="container">
      <div className="card">
        <div className="cardHeader">
          <div>
            <h1 className="title">Operations Dashboard</h1>
            <p className="sub">
              Controls the automation loop: IMAP ingest → Regex → Gemini → Human Review → Order + Confirmation.
            </p>
          </div>

          <span className="badge">
            <span className={`dot ${enabled ? "good" : "bad"}`} />
            {enabled ? "Agent Running" : "Agent Stopped"}
          </span>
        </div>

        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn btnPrimary" onClick={start} disabled={enabled}>Start Agent</button>
          <button className="btn btnDanger" onClick={stop} disabled={!enabled}>Stop</button>
          <button className="btn" onClick={load}>Refresh</button>
        </div>

        <div className="kpiRow">
          <div className="kpi">
            <b>Auto-refresh</b>
            <span>Inbox updates every 5s</span>
          </div>
          <div className="kpi">
            <b>Automation tick</b>
            <span>Runs every 15s (Celery Beat)</span>
          </div>
          <div className="kpi">
            <b>Fallback safety</b>
            <span>Human review for missing fields</span>
          </div>
        </div>
      </div>
    </div>
  );
}