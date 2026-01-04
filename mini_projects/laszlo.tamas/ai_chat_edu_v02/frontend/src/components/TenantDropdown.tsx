import { useEffect, useState } from "react";
import { Tenant } from "../types";
import { fetchTenants } from "../api";
import "./TenantDropdown.css";

interface TenantDropdownProps {
  selectedTenantId: number | null;
  onTenantChange: (tenantId: number) => void;
}

export function TenantDropdown({ selectedTenantId, onTenantChange }: TenantDropdownProps) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    fetchTenants(true) // Only active tenants
      .then((data) => {
        setTenants(data);
        // Auto-select first tenant if none selected
        if (!selectedTenantId && data.length > 0) {
          onTenantChange(data[0].id);
        }
      })
      .catch((err) => {
        console.error("Failed to load tenants:", err);
        setError("Failed to load tenants");
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <div className="tenant-dropdown loading">Loading tenants...</div>;
  }

  if (error) {
    return <div className="tenant-dropdown error">{error}</div>;
  }

  return (
    <div className="tenant-dropdown">
      <label htmlFor="tenant-select">🏢 Tenant:</label>
      <select
        id="tenant-select"
        value={selectedTenantId || ""}
        onChange={(e) => onTenantChange(Number(e.target.value))}
      >
        {tenants.map((tenant) => (
          <option key={tenant.id} value={tenant.id}>
            {tenant.name} ({tenant.key})
          </option>
        ))}
      </select>
    </div>
  );
}
