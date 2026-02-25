import { useEffect, useState } from "react";
import { api } from "../api";

function dot(ok){ return ok ? "good" : "bad"; }

export default function Settings() {
  const [status, setStatus] = useState(null);
  const [msg, setMsg] = useState("");

  async function load(){
    setMsg("");
    const res = await api.get("/settings/status");
    setStatus(res.data);
  }

  async function testImap(){
    setMsg("Testing IMAP...");
    try{
      const r = await api.post("/settings/test-imap");
      setMsg(`IMAP OK. Unseen found: ${r.data.unseen_found}`);
      load();
    }catch(e){
      setMsg("IMAP test failed. Check IMAP_HOST/USER/PASSWORD and Gmail App Password.");
    }
  }

  async function testSmtp(){
    setMsg("Testing SMTP (sending test mail to SMTP_USER)...");
    try{
      const r = await api.post("/settings/test-smtp");
      setMsg(`SMTP OK. Sent to: ${r.data.sent_to}`);
      load();
    }catch(e){
      setMsg("SMTP test failed. Check SMTP_HOST/USER/PASSWORD and App Password.");
    }
  }

  async function testGemini(){
    setMsg("Testing Gemini...");
    try{
      const r = await api.post("/settings/test-gemini");
      if (!r.data.ok) setMsg(`Gemini not ready: ${r.data.error}`);
      else setMsg(`Gemini OK: ${r.data.response}`);
      load();
    }catch(e){
      setMsg("Gemini test failed. Check GEMINI_API_KEY.");
    }
  }

  useEffect(() => { load(); }, []);

  const role = localStorage.getItem("role") || "viewer";
  if (role !== "admin"){
    return (
      <div className="container">
        <div className="card">
          <h1 className="title">Settings</h1>
          <p className="sub">Access denied. Only ADMIN can view configuration and run connectivity tests.</p>
        </div>
      </div>
    );
  }

  if (!status){
    return <div className="container"><div className="card">Loading...</div></div>;
  }

  return (
    <div className="container">
      <div className="card">
        <div className="cardHeader">
          <div>
            <h1 className="title">System Configuration</h1>
            <p className="sub">Live config validation + connectivity tests (IMAP/SMTP/Gemini).</p>
          </div>
          <button className="btn" onClick={load}>Refresh</button>
        </div>

        <div className="kpiRow">
          <span className="badge"><span className={`dot ${dot(status.imap.ok)}`} />IMAP {status.imap.ok ? "READY" : "MISSING"}</span>
          <span className="badge"><span className={`dot ${dot(status.smtp.ok)}`} />SMTP {status.smtp.ok ? "READY" : "MISSING"}</span>
          <span className="badge"><span className={`dot ${dot(status.gemini.ok)}`} />GEMINI {status.gemini.ok ? "READY" : "OFF"}</span>
        </div>

        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn btnPrimary" onClick={testImap}>Test IMAP</button>
          <button className="btn btnPrimary" onClick={testSmtp}>Test SMTP</button>
          <button className="btn btnPrimary" onClick={testGemini}>Test Gemini</button>
        </div>

        {msg ? <div className="toast">{msg}</div> : null}
      </div>

      <div className="grid2" style={{ marginTop: 14 }}>
        <div className="card">
          <h2 className="title" style={{ fontSize: 18 }}>Live Config View (masked)</h2>
          <table className="table" style={{ marginTop: 12 }}>
            <thead>
              <tr><th>Key</th><th>Value</th></tr>
            </thead>
            <tbody>
              <tr><td className="mono">IMAP_HOST</td><td className="mono">{status.imap.host}</td></tr>
              <tr><td className="mono">IMAP_USER</td><td className="mono">{status.imap.user}</td></tr>
              <tr><td className="mono">IMAP_FOLDER</td><td className="mono">{status.imap.folder}</td></tr>
              <tr><td className="mono">IMAP_PASSWORD</td><td className="mono">{status.env_masked.IMAP_PASSWORD}</td></tr>

              <tr><td className="mono">SMTP_HOST</td><td className="mono">{status.smtp.host}</td></tr>
              <tr><td className="mono">SMTP_PORT</td><td className="mono">{status.smtp.port}</td></tr>
              <tr><td className="mono">SMTP_USER</td><td className="mono">{status.smtp.user}</td></tr>
              <tr><td className="mono">SMTP_FROM</td><td className="mono">{status.smtp.from}</td></tr>
              <tr><td className="mono">SMTP_PASSWORD</td><td className="mono">{status.env_masked.SMTP_PASSWORD}</td></tr>

              <tr><td className="mono">GEMINI_MODEL</td><td className="mono">{status.gemini.model}</td></tr>
              <tr><td className="mono">GEMINI_API_KEY</td><td className="mono">{status.env_masked.GEMINI_API_KEY}</td></tr>

              <tr><td className="mono">JWT_SECRET</td><td className="mono">{status.env_masked.JWT_SECRET}</td></tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2 className="title" style={{ fontSize: 18 }}>Operational Notes</h2>
          <p className="sub">
            • IMAP must point to a server (e.g., <span className="mono">imap.gmail.com</span>)<br/>
            • Gmail requires App Password (2FA enabled)<br/>
            • SMTP test sends mail to <span className="mono">SMTP_USER</span><br/>
            • Gemini triggers when Regex misses fields<br/>
          </p>

          <div className="kpiRow" style={{ marginTop: 12 }}>
            <div className="kpi"><b>Security</b><span>Passwords are masked</span></div>
            <div className="kpi"><b>Access</b><span>Admin/Reviewer roles</span></div>
            <div className="kpi"><b>Telemetry</b><span>Live activity feed</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}