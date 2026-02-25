import { useEffect, useState } from "react";
import { api } from "../api";

function iconFor(t){
  if (t === "email") return "📨";
  if (t === "order") return "🧾";
  return "🧠";
}

export default function Activity() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");

  async function load(){
    setErr("");
    try{
      const res = await api.get("/activity/recent");
      setItems(res.data.timeline || []);
    }catch(e){
      setErr("Failed to load activity feed.");
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="container">
      <div className="card">
        <div className="cardHeader">
          <div>
            <h1 className="title">Activity Timeline</h1>
            <p className="sub">Live operational events (auto-refresh every 5s).</p>
          </div>
          <button className="btn" onClick={load}>Refresh</button>
        </div>

        {err ? <div className="toast" style={{ borderColor:"rgba(239,68,68,.22)" }}>{err}</div> : null}

        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Type</th>
              <th>Time</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {items.map((x, idx) => (
              <tr key={idx}>
                <td className="mono">{iconFor(x.type)} {x.type}</td>
                <td className="mono">{new Date(x.time).toLocaleString()}</td>
                <td>
                  {x.type === "email" ? (
                    <span className="mono">Email #{x.email_id} • {x.status} • {x.subject}</span>
                  ) : x.type === "order" ? (
                    <span className="mono">{x.job_id} • {x.customer_name} • {x.weight_kg}kg</span>
                  ) : (
                    <span className="mono">Email #{x.email_id} • layer={x.layer} • missing={JSON.stringify(x.missing)}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {items.length === 0 ? <p className="sub" style={{ marginTop: 12 }}>No activity yet.</p> : null}
      </div>
    </div>
  );
}