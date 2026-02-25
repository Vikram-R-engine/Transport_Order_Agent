import { useEffect, useState } from "react";
import { api } from "../api";

export default function ReviewQueue() {
  const [queue, setQueue] = useState([]);
  const [form, setForm] = useState({}); // emailId -> fields json string

  async function load() {
    const res = await api.get("/review/queue");
    setQueue(res.data);
  }

  async function submit(emailId) {
    let obj = {};
    try {
      obj = JSON.parse(form[emailId] || "{}");
    } catch {
      alert("Invalid JSON in proposed fields");
      return;
    }
    await api.post(`/review/${emailId}/submit`, { proposed_fields: obj, reviewer: "human" });
    alert("Submitted. If complete, order creation will run automatically.");
    load();
  }

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h2>Human Review Queue</h2>
      <button onClick={load}>Refresh</button>

      <div style={{ marginTop: 12 }}>
        {queue.map((e) => (
          <div key={e.id} style={{ padding: 12, border: "1px solid #ddd", borderRadius: 10, marginBottom: 12 }}>
            <div><b>{e.subject || "(no subject)"}</b></div>
            <div style={{ opacity: 0.8 }}>{e.from_email}</div>
            <div><b>Missing:</b> {(e.missing_fields || []).join(", ")}</div>

            <div style={{ marginTop: 10 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Proposed fields (JSON)</div>
              <textarea
                rows={6}
                style={{ width: "100%", padding: 10 }}
                placeholder='{"customer_name":"John","weight_kg":25,"pickup_location":"Chennai","drop_location":"Bangalore","pickup_time_window":"Tomorrow 10am-6pm"}'
                value={form[e.id] || ""}
                onChange={(ev) => setForm({ ...form, [e.id]: ev.target.value })}
              />
              <button onClick={() => submit(e.id)} style={{ marginTop: 8 }}>Submit & Approve</button>
            </div>
          </div>
        ))}
        {queue.length === 0 ? <div style={{ opacity: 0.7 }}>No items in review queue.</div> : null}
      </div>
    </div>
  );
}