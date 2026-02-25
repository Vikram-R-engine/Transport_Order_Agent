import { useEffect, useState } from "react";
import { api } from "../api";

export default function Orders() {
  const [orders, setOrders] = useState([]);

  async function load() {
    const res = await api.get("/orders");
    setOrders(res.data);
  }

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h2>Orders</h2>
      <button onClick={load}>Refresh</button>

      <div style={{ marginTop: 12 }}>
        {orders.map((o) => (
          <div key={o.id} style={{ padding: 12, border: "1px solid #ddd", borderRadius: 10, marginBottom: 10 }}>
            <div><b>{o.job_id}</b> — {o.customer_name}</div>
            <div>Weight: {o.weight_kg} kg</div>
            <div>Pickup: {o.pickup_location}</div>
            <div>Drop: {o.drop_location}</div>
            <div>Window: {o.pickup_time_window}</div>
          </div>
        ))}
        {orders.length === 0 ? <div style={{ opacity: 0.7 }}>No orders yet.</div> : null}
      </div>
    </div>
  );
}