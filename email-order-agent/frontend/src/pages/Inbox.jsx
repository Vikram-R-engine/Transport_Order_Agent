import { useEffect, useState } from "react";
import { api } from "../api";
import { Link } from "react-router-dom";

function statusDot(status){
  if (status?.includes("REVIEW")) return "warn";
  if (status?.includes("FAILED")) return "bad";
  if (status?.includes("SENT") || status?.includes("CREATED")) return "good";
  return "dot";
}

export default function Inbox() {
  const [emails, setEmails] = useState([]);

  async function load() {
    const res = await api.get("/emails");
    setEmails(res.data);
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
            <h1 className="title">Inbox</h1>
            <p className="sub">Auto-refresh every 5 seconds. New emails will appear here.</p>
          </div>
          <button className="btn" onClick={load}>Refresh</button>
        </div>

        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Status</th>
              <th>Subject</th>
              <th>From</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {emails.map((e) => (
              <tr key={e.id}>
                <td>
                  <span className="badge">
                    <span className={`dot ${statusDot(e.status)}`} />
                    {e.status}
                  </span>
                </td>
                <td>{e.subject || "(no subject)"}</td>
                <td className="mono">{e.from_email}</td>
                <td><Link className="tab active" to={`/emails/${e.id}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>

        {emails.length === 0 ? <p className="sub" style={{ marginTop: 12 }}>No emails yet.</p> : null}
      </div>
    </div>
  );
}