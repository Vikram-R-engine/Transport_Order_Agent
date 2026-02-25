import { useEffect, useState } from "react";
import { api } from "../api";
import { useParams } from "react-router-dom";
import FieldTable from "../components/FieldTable";

export default function EmailDetail() {
  const { id } = useParams();
  const [email, setEmail] = useState(null);

  async function load() {
    const res = await api.get(`/emails/${id}`);
    setEmail(res.data);
  }

  async function processNow() {
    await api.post(`/emails/${id}/process`);
    alert("Processing started. Refresh in a few seconds.");
  }

  useEffect(() => { load(); }, [id]);

  if (!email) return <div className="container"><div className="card">Loading...</div></div>;

  return (
    <div className="container">
      <div className="grid2">
        <div className="card">
          <div className="cardHeader">
            <div>
              <h1 className="title">Email #{email.id}</h1>
              <p className="sub">Extraction + order creation status for this email.</p>
            </div>
            <span className="badge">
              <span className={`dot ${email.status?.includes("REVIEW") ? "warn" : (email.status?.includes("FAILED") ? "bad" : "good")}`} />
              {email.status}
            </span>
          </div>

          <div style={{ marginTop: 12 }}>
            <div className="kpi"><span className="sub">From</span><b className="mono">{email.from_email}</b></div>
            <div className="kpi" style={{ marginTop: 10 }}><span className="sub">Subject</span><b>{email.subject || "(no subject)"}</b></div>
            {email.last_error ? (
              <div className="kpi" style={{ marginTop: 10, borderColor: "rgba(239,68,68,.35)" }}>
                <span className="sub">Error</span>
                <b style={{ color: "#fecaca" }}>{email.last_error}</b>
              </div>
            ) : null}
          </div>

          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn btnPrimary" onClick={processNow}>Run Extraction Now</button>
            <button className="btn" onClick={load}>Refresh</button>
          </div>
        </div>

        <div className="card">
          <h2 className="title" style={{ fontSize: 18 }}>Extracted Fields</h2>
          <FieldTable extracted={email.extracted} missing={email.missing_fields} />
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h2 className="title" style={{ fontSize: 18 }}>Email Body</h2>
        <pre className="mono" style={{ whiteSpace: "pre-wrap" }}>
{email.body_text || "(empty)"}
        </pre>
      </div>
    </div>
  );
}