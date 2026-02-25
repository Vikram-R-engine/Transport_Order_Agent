import { useState } from "react";
import { api } from "../api";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const nav = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
     const res = await api.post("/auth/login", { username, password });
localStorage.setItem("token", res.data.access_token);
localStorage.setItem("role", res.data.role || "viewer");
nav("/");
    } catch {
      setErr("Invalid credentials");
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", border: "1px solid #ddd", borderRadius: 12, padding: 16 }}>
      <h2>Login</h2>
      <form onSubmit={submit}>
        <div style={{ marginBottom: 10 }}>
          <div>Username</div>
          <input value={username} onChange={(e)=>setUsername(e.target.value)} style={{ width: "100%", padding: 10 }} />
        </div>
        <div style={{ marginBottom: 10 }}>
          <div>Password</div>
          <input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} style={{ width: "100%", padding: 10 }} />
        </div>
        {err && <div style={{ color: "crimson", marginBottom: 10 }}>{err}</div>}
        <button style={{ padding: "10px 12px" }}>Login</button>
      </form>
      <p style={{ marginTop: 12, opacity: 0.8 }}>
        Demo credentials: <b>admin / admin123</b> (from backend/.env)
      </p>
    </div>
  );
}