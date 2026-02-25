export default function FieldTable({ extracted, missing }) {
  const keys = ["customer_name", "weight_kg", "pickup_location", "drop_location", "pickup_time_window"];
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Field</th>
          <th>Value</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((k) => {
          const isMissing = (missing || []).includes(k);
          return (
            <tr key={k}>
              <td><b>{k}</b></td>
              <td className="mono">{String(extracted?.[k] ?? "")}</td>
              <td>
                <span className="badge">
                  <span className={`dot ${isMissing ? "bad" : "good"}`} />
                  {isMissing ? "Missing" : "OK"}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}